import sys
from pathlib import Path

import polib

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.i18n.action_split_rules import get_action_target_file
from tools.i18n.split_action_module import build_split_outputs


def make_po(entries: dict[str, str]) -> polib.POFile:
    po = polib.POFile()
    po.metadata = {
        "Content-Type": "text/plain; charset=UTF-8",
        "Language": "zh_CN",
    }
    for msgid, msgstr in entries.items():
        po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
    return po


def test_action_split_rules_route_expected_msgids():
    assert get_action_target_file("attack_action_name") == "action_combat.po"
    assert get_action_target_file("breakthrough_action_name") == "action_progression.po"
    assert get_action_target_file("move_to_region_action_name") == "action_world.po"
    assert get_action_target_file("action_reading") == "action.po"


def test_build_split_outputs_preserves_entries_and_metadata():
    source = make_po(
        {
            "attack_action_name": "发起战斗",
            "breakthrough_action_name": "突破",
            "move_to_region_action_name": "前往区域",
            "action_reading": "读书",
        }
    )

    outputs = build_split_outputs(source)

    assert set(outputs.keys()) == {
        "action.po",
        "action_combat.po",
        "action_progression.po",
        "action_world.po",
    }

    assert outputs["action_combat.po"].metadata["Language"] == "zh_CN"
    assert [entry.msgid for entry in outputs["action_combat.po"]] == ["attack_action_name"]
    assert [entry.msgid for entry in outputs["action_progression.po"]] == ["breakthrough_action_name"]
    assert [entry.msgid for entry in outputs["action_world.po"]] == ["move_to_region_action_name"]
    assert [entry.msgid for entry in outputs["action.po"]] == ["action_reading"]

    all_msgids = []
    for po in outputs.values():
        all_msgids.extend(entry.msgid for entry in po)
    assert sorted(all_msgids) == sorted(
        [
            "attack_action_name",
            "breakthrough_action_name",
            "move_to_region_action_name",
            "action_reading",
        ]
    )
