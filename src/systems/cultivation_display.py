from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.i18n import t
from src.systems.cultivation import Realm, Stage
from src.utils.df import game_configs, get_str


DEFAULT_PROFILE_ID = "dao"
ROGUE_PROFILE_ID = "sanxiu"
YAO_PROFILE_ID = "yao"


@dataclass(frozen=True)
class CultivationAliasEntry:
    profile_id: str
    realm_id: str
    stage_id: str
    realm_name_id: str
    stage_name_id: str
    full_name_id: str


def _load_alias_entries() -> dict[tuple[str, str, str], CultivationAliasEntry]:
    entries: dict[tuple[str, str, str], CultivationAliasEntry] = {}
    for row in game_configs.get("cultivation_alias", []) or []:
        profile_id = get_str(row, "profile_id")
        realm_id = get_str(row, "realm_key")
        stage_id = get_str(row, "stage_key")
        if not profile_id or not realm_id or not stage_id:
            continue
        entry = CultivationAliasEntry(
            profile_id=profile_id,
            realm_id=realm_id,
            stage_id=stage_id,
            realm_name_id=get_str(row, "realm_name_id"),
            stage_name_id=get_str(row, "stage_name_id"),
            full_name_id=get_str(row, "full_name_id"),
        )
        entries[(profile_id, realm_id, stage_id)] = entry
    return entries


def _alias_entries() -> dict[tuple[str, str, str], CultivationAliasEntry]:
    # Read from game_configs at call time so tests and config reloads can patch it.
    return _load_alias_entries()


def _translate_or_empty(msgid: str) -> str:
    if not msgid:
        return ""
    translated = t(msgid)
    return "" if translated == msgid else translated


def _join_realm_stage(realm_name: str, stage_name: str) -> str:
    if not realm_name:
        return stage_name
    if not stage_name:
        return realm_name
    return f"{realm_name}{stage_name}"


def resolve_cultivation_alias_profile(avatar: Any) -> str:
    from src.classes.race import is_yao_avatar

    if is_yao_avatar(avatar):
        return YAO_PROFILE_ID

    raw_orthodoxy_id = getattr(getattr(avatar, "orthodoxy", None), "id", "")
    orthodoxy_id = raw_orthodoxy_id if isinstance(raw_orthodoxy_id, str) else ""
    if orthodoxy_id:
        return orthodoxy_id
    return ROGUE_PROFILE_ID


def build_cultivation_display(cultivation_progress: Any, *, profile_id: str) -> dict[str, Any]:
    realm = getattr(cultivation_progress, "realm", Realm.Qi_Refinement)
    stage = getattr(cultivation_progress, "stage", Stage.Early_Stage)
    level = int(getattr(cultivation_progress, "level", 0) or 0)

    if not isinstance(realm, Realm):
        realm = getattr(realm, "value", realm)
        try:
            realm = Realm(str(realm))
        except ValueError:
            realm = Realm.from_str(str(realm))
    if not isinstance(stage, Stage):
        stage = getattr(stage, "value", stage)
        try:
            stage = Stage(str(stage))
        except ValueError:
            stage = Stage.from_str(str(stage))

    realm_id = realm.value
    stage_id = stage.value
    canonical_realm_name = str(realm)
    canonical_stage_name = str(stage)
    canonical_full_name = _join_realm_stage(canonical_realm_name, canonical_stage_name)

    entries = _alias_entries()
    entry = (
        entries.get((profile_id, realm_id, stage_id))
        or entries.get((DEFAULT_PROFILE_ID, realm_id, stage_id))
    )

    display_realm_name = canonical_realm_name
    display_stage_name = canonical_stage_name
    display_full_name = canonical_full_name
    resolved_profile_id = profile_id if entry and entry.profile_id == profile_id else DEFAULT_PROFILE_ID

    if entry:
        display_realm_name = _translate_or_empty(entry.realm_name_id) or canonical_realm_name
        display_stage_name = _translate_or_empty(entry.stage_name_id) or canonical_stage_name
        display_full_name = (
            _translate_or_empty(entry.full_name_id)
            or _join_realm_stage(display_realm_name, display_stage_name)
        )

    profile_name = _translate_or_empty(f"cultivation_alias.profile.{resolved_profile_id}") or resolved_profile_id

    return {
        "profile_id": resolved_profile_id,
        "profile_name": profile_name,
        "realm_id": realm_id,
        "stage_id": stage_id,
        "level": level,
        "canonical_realm_name": canonical_realm_name,
        "canonical_stage_name": canonical_stage_name,
        "canonical_full_name": canonical_full_name,
        "display_realm_name": display_realm_name,
        "display_stage_name": display_stage_name,
        "display_full_name": display_full_name,
    }


def build_avatar_cultivation_display(avatar: Any) -> dict[str, Any]:
    return build_cultivation_display(
        getattr(avatar, "cultivation_progress", None),
        profile_id=resolve_cultivation_alias_profile(avatar),
    )


def build_avatar_cultivation_summary(avatar: Any) -> dict[str, Any]:
    display = build_avatar_cultivation_display(avatar)
    return {
        "realm_id": display["realm_id"],
        "stage_id": display["stage_id"],
        "profile_id": display["profile_id"],
        "display_full_name": display["display_full_name"],
        "canonical_full_name": display["canonical_full_name"],
    }
