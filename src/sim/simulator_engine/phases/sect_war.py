from __future__ import annotations

from src.classes.event import Event
from src.classes.observe import is_within_observation
from src.systems.battle import decide_battle, get_effective_strength_pair, handle_battle_finish
from src.i18n import t


def _pair_key(a_id: str, b_id: str) -> tuple[str, str]:
    a = str(a_id)
    b = str(b_id)
    return (a, b) if a <= b else (b, a)


def _teleport_avatar_to_sect_headquarter(avatar, sect_manager) -> bool:
    sect = getattr(avatar, "sect", None)
    world = getattr(avatar, "world", None)
    if sect is None or world is None:
        return False

    snapshot = sect_manager.get_snapshot()
    center = snapshot.sect_centers.get(int(getattr(sect, "id", 0)))
    if center is None:
        return False

    x, y = center
    avatar.pos_x = x
    avatar.pos_y = y
    avatar.tile = world.map.get_tile(x, y)
    return avatar.tile is not None


async def phase_handle_sect_wars(simulator, living_avatars) -> list[Event]:
    world = simulator.world
    sect_manager = simulator.sect_manager
    events: list[Event] = []
    engaged_avatar_ids: set[str] = set()
    processed_pairs: set[tuple[str, str]] = set()

    for idx in range(len(living_avatars)):
        attacker = living_avatars[idx]
        attacker_sect = getattr(attacker, "sect", None)
        if attacker_sect is None or getattr(attacker, "is_dead", False):
            continue
        if str(attacker.id) in engaged_avatar_ids:
            continue

        for jdx in range(idx + 1, len(living_avatars)):
            defender = living_avatars[jdx]
            defender_sect = getattr(defender, "sect", None)
            if defender_sect is None or defender_sect == attacker_sect:
                continue
            if getattr(defender, "is_dead", False) or str(defender.id) in engaged_avatar_ids:
                continue
            if not world.are_sects_at_war(int(attacker_sect.id), int(defender_sect.id)):
                continue
            if not (is_within_observation(attacker, defender) or is_within_observation(defender, attacker)):
                continue

            avatar_pair = _pair_key(attacker.id, defender.id)
            if avatar_pair in processed_pairs:
                continue
            processed_pairs.add(avatar_pair)

            s_att, s_def = get_effective_strength_pair(attacker, defender)
            start_text = (
                f"{attacker_sect.name} 与 {defender_sect.name} 交战中，"
                f"{attacker.name} 与 {defender.name} 狭路相逢，立即爆发战斗"
                f"（战力：{attacker.name} {int(s_att)} vs {defender.name} {int(s_def)}）。"
            )
            events.append(
                Event(
                    month_stamp=world.month_stamp,
                    content=start_text,
                    related_avatars=[attacker.id, defender.id],
                    related_sects=[int(attacker_sect.id), int(defender_sect.id)],
                    is_major=True,
                )
            )

            winner, loser, loser_damage, winner_damage = decide_battle(attacker, defender)
            loser.hp.reduce(loser_damage)
            winner.hp.reduce(winner_damage)

            war_events = await handle_battle_finish(
                world,
                attacker,
                defender,
                (winner, loser, loser_damage, winner_damage),
                start_text,
                "请描写一次宗门战争中的遭遇战，突出双方所属宗门的敌意与战场余波。",
                check_loot=False,
            )
            for event in war_events:
                event.related_sects = [int(attacker_sect.id), int(defender_sect.id)]
            events.extend(war_events)
            world.record_sect_battle(int(attacker_sect.id), int(defender_sect.id))
            if getattr(loser, "sect", None) is not None:
                loser.sect.change_war_weariness(3)

            contribution_gain = 40 if getattr(loser, "is_dead", False) else 25
            actual_gain = winner.add_sect_contribution(contribution_gain)
            if actual_gain > 0 and getattr(winner, "sect", None) is not None:
                events.append(
                    Event(
                        month_stamp=world.month_stamp,
                        content=t(
                            "{winner_name} distinguished themselves in sect war and earned {amount} sect contribution for {sect_name}.",
                            winner_name=winner.name,
                            amount=actual_gain,
                            sect_name=winner.sect.name,
                        ),
                        related_avatars=[winner.id],
                        related_sects=[int(attacker_sect.id), int(defender_sect.id)],
                        is_major=False,
                    )
                )

            if not getattr(loser, "is_dead", False) and _teleport_avatar_to_sect_headquarter(loser, sect_manager):
                events.append(
                    Event(
                        month_stamp=world.month_stamp,
                        content=f"{loser.name} 战败后被迫撤回 {loser.sect.name} 总部休整。",
                        related_avatars=[loser.id],
                        related_sects=[int(attacker_sect.id), int(defender_sect.id)],
                        is_major=False,
                    )
                )

            engaged_avatar_ids.add(str(attacker.id))
            engaged_avatar_ids.add(str(defender.id))
            break

    return events
