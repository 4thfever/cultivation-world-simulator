from __future__ import annotations

import json
from pathlib import Path

from src.i18n.locale_registry import get_locale_codes


def test_wiki_generate_outputs_locale_payloads(tmp_path: Path):
    from tools.wiki.generate import generate

    output_dir = tmp_path / "wiki"
    generated = generate(output_dir)

    expected_locales = get_locale_codes()
    assert sorted(generated) == sorted(expected_locales)

    registry_path = output_dir / "data" / "registry.json"
    assert registry_path.exists()

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert sorted(entry["code"] for entry in registry["locales"]) == sorted(expected_locales)

    for locale in expected_locales:
        payload_path = output_dir / "data" / f"{locale}.json"
        assert payload_path.exists()

        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        assert payload["locale"] == locale
        assert set(payload["tabs"]) >= {
            "world",
            "actions",
            "personas",
            "sects",
            "orthodoxies",
            "races",
            "techniques",
            "weapons",
            "auxiliaries",
            "elixirs",
            "materials",
            "animals",
            "plants",
            "lodes",
            "hidden_domains",
            "sect_tasks",
            "regions",
        }
    assert payload["tabs"]["world"]["items"]
    assert payload["tabs"]["actions"]["items"]
    assert payload["tabs"]["personas"]["items"]
    assert payload["tabs"]["sects"]["items"]
    assert payload["tabs"]["regions"]["items"]["normal"]["title"]
    assert payload["tabs"]["regions"]["items"]["sect"]["title"]


def test_wiki_generate_actions_match_registry(tmp_path: Path):
    from tools.wiki.generate import generate
    from src.classes.action.registry import ActionRegistry
    import src.classes.action  # noqa: F401
    import src.classes.mutual_action  # noqa: F401

    output_dir = tmp_path / "wiki"
    generate(output_dir)

    payload = json.loads((output_dir / "data" / "zh-CN.json").read_text(encoding="utf-8"))
    action_items = payload["tabs"]["actions"]["items"]

    assert len(action_items) == len(list(ActionRegistry.all_actual()))

    sample = next(item for item in action_items if item["id"] == "MoveToRegion")
    assert sample["name"]
    assert sample["desc"]
    assert sample["requirements"] is not None
    assert "param_sources" in sample
    assert "module" in sample


def test_wiki_generate_adds_meta_and_theme_fields(tmp_path: Path):
    from tools.wiki.generate import generate

    output_dir = tmp_path / "wiki"
    generate(output_dir)

    payload = json.loads((output_dir / "data" / "zh-CN.json").read_text(encoding="utf-8"))

    persona = payload["tabs"]["personas"]["items"][0]
    sect = payload["tabs"]["sects"]["items"][0]
    weapon = payload["tabs"]["weapons"]["items"][0]
    technique = payload["tabs"]["techniques"]["items"][0]

    assert persona["meta"]["category"] == "persona"
    assert "theme" in persona
    assert "rarity" in persona
    assert "completeness" in persona

    assert sect["meta"]["category"] == "sect"
    assert "relations" in sect
    assert "completeness" in sect

    assert weapon["meta"]["category"] == "weapon"
    assert "theme" in weapon
    assert "rarity" in weapon
    assert "completeness" in weapon

    assert technique["meta"]["category"] == "technique"
    assert technique["grade"]
    assert technique["theme"].startswith("grade-")


def test_wiki_generate_elixirs_include_realm(tmp_path: Path):
    from tools.wiki.generate import generate

    output_dir = tmp_path / "wiki"
    generate(output_dir)

    payload = json.loads((output_dir / "data" / "zh-CN.json").read_text(encoding="utf-8"))
    elixir = payload["tabs"]["elixirs"]["items"][0]

    assert elixir["realm"]
    assert elixir["completeness"]["complete"] is True
    assert "realm" not in elixir["completeness"]["missing"]


def test_wiki_generate_item_and_resource_categories_are_tabs(tmp_path: Path):
    from tools.wiki.generate import generate

    output_dir = tmp_path / "wiki"
    generate(output_dir)

    payload = json.loads((output_dir / "data" / "zh-CN.json").read_text(encoding="utf-8"))

    assert "items" not in payload["tabs"]
    assert "resources" not in payload["tabs"]
    for key in ("weapons", "auxiliaries", "elixirs", "materials", "animals", "plants", "lodes"):
        assert payload["tabs"][key]["kind"] == "list"
        assert payload["tabs"][key]["items"]


def test_wiki_generate_keeps_only_useful_relations(tmp_path: Path):
    from tools.wiki.generate import generate

    output_dir = tmp_path / "wiki"
    generate(output_dir)

    payload = json.loads((output_dir / "data" / "zh-CN.json").read_text(encoding="utf-8"))

    weapon = payload["tabs"]["weapons"]["items"][0]
    elixir = payload["tabs"]["elixirs"]["items"][0]
    animal = next(item for item in payload["tabs"]["animals"]["items"] if item.get("relations"))

    assert "relations" not in weapon
    assert "relations" not in elixir
    assert animal["relations"]["materials"]
    assert animal["relations"]["materials"][0] == animal["drops"][0]["name"]


def test_wiki_generate_hidden_domains_and_sect_tasks(tmp_path: Path):
    from tools.wiki.generate import generate

    output_dir = tmp_path / "wiki"
    generate(output_dir)

    payload = json.loads((output_dir / "data" / "zh-CN.json").read_text(encoding="utf-8"))
    hidden_domain = payload["tabs"]["hidden_domains"]["items"][0]
    sect_task = payload["tabs"]["sect_tasks"]["items"][0]

    assert hidden_domain["name"]
    assert hidden_domain["required_realm"]
    assert hidden_domain["completeness"]["complete"] is True
    assert hidden_domain["meta"]["category"] == "hidden_domain"
    assert "relations" not in hidden_domain

    assert sect_task["title"]
    assert sect_task["allowed_realms"]
    assert sect_task["base_success"]
    assert sect_task["reward_stone_per_month"]
    assert sect_task["meta"]["category"] == "sect_task"
    assert "relations" not in sect_task


def test_wiki_generate_attaches_images_and_copies_assets(tmp_path: Path):
    from tools.wiki.generate import generate

    output_dir = tmp_path / "wiki"
    generate(output_dir)

    payload = json.loads((output_dir / "data" / "zh-CN.json").read_text(encoding="utf-8"))

    world_info = payload["tabs"]["world"]["items"][0]
    sect = next(item for item in payload["tabs"]["sects"]["items"] if str(item["id"]) == "1")
    city_group = payload["tabs"]["regions"]["items"]["city"]["items"]
    city = next(item for item in city_group if str(item["id"]) == "301")

    assert "cover_image" not in world_info
    assert "images" not in world_info
    assert sect["cover_image"]["src"].startswith("./assets/sects/sect_1")
    assert sect["images"]
    assert city["cover_image"]["src"].startswith("./assets/cities/city_301")
    assert any(image["src"].startswith("./assets/cities/city_301") for image in city["images"])
    assert city["images"]

    copied_sect = output_dir / "assets" / "sects" / "sect_1.png"
    copied_city = output_dir / "assets" / "cities" / "city_301_0.png"

    assert copied_sect.exists()
    assert copied_city.exists()


def test_wiki_generate_keeps_text_only_sections_without_decorative_images(tmp_path: Path):
    from tools.wiki.generate import generate

    output_dir = tmp_path / "wiki"
    generate(output_dir)

    payload = json.loads((output_dir / "data" / "zh-CN.json").read_text(encoding="utf-8"))
    world_info = payload["tabs"]["world"]["items"][0]
    race = next(item for item in payload["tabs"]["races"]["items"] if item["id"] == "human")

    assert "cover_image" not in world_info
    assert "images" not in world_info
    assert "cover_image" not in race
    assert "images" not in race


def test_wiki_serve_generates_once_when_inputs_match(tmp_path: Path, monkeypatch):
    import tools.wiki.serve as serve

    calls: list[Path] = []

    def fake_generate(output_dir: Path) -> list[str]:
        calls.append(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
        data_dir = output_dir / "data"
        data_dir.mkdir()
        (data_dir / "registry.json").write_text("{}", encoding="utf-8")
        return ["zh-CN"]

    monkeypatch.setattr(serve, "build_input_fingerprint", lambda: "same-inputs")
    monkeypatch.setattr(serve, "generate", fake_generate)

    output_dir = tmp_path / "wiki"

    regenerated, locales = serve.ensure_generated(output_dir)
    assert regenerated is True
    assert locales == ["zh-CN"]
    assert len(calls) == 1

    regenerated, locales = serve.ensure_generated(output_dir)
    assert regenerated is False
    assert locales == ["zh-CN"]
    assert len(calls) == 1

    manifest = serve.read_manifest(output_dir)
    assert manifest["input_hash"] == "same-inputs"
