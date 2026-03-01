from typing import List, Dict, TYPE_CHECKING
import random

from src.classes.gathering.gathering import Gathering, register_gathering
from src.classes.event import Event
from src.systems.time import Month
from src.systems.cultivation import Realm
from src.systems.battle import decide_battle, get_base_strength

if TYPE_CHECKING:
    from src.classes.core.world import World
    from src.classes.core.avatar import Avatar

@register_gathering
class Tournament(Gathering):
    """
    天下武道会事件
    """
    
    # LLM Prompt ID
    STORY_PROMPT_ID = "tournament_story_prompt"

    def is_start(self, world: "World") -> bool:
        """
        十年一次。第一次在游戏开始第2年。
        """
        year = world.month_stamp.get_year()
        month = world.month_stamp.get_month()
        
        if month != Month.JANUARY:
            return False
            
        target_first_year = world.start_year + 1
        if year >= target_first_year and (year - target_first_year) % 10 == 0:
            return True
            
        return False

    def get_related_avatars(self, world: "World") -> List[int]:
        # 所有存活角色都有资格
        return [avatar.id for avatar in world.avatar_manager.get_living_avatars()]

    def get_info(self, world: "World") -> str:
        from src.i18n import t
        return t("World Martial Arts Tournament is in progress...")

    async def execute(self, world: "World") -> List[Event]:
        from src.i18n import t
        events = []
        
        living_avatars = world.avatar_manager.get_living_avatars()
        
        heaven = []
        earth = []
        human = []
        
        for avatar in living_avatars:
            if avatar.cultivation_progress.realm == Realm.Nascent_Soul:
                heaven.append(avatar)
            elif avatar.cultivation_progress.realm == Realm.Core_Formation:
                earth.append(avatar)
            elif avatar.cultivation_progress.realm == Realm.Foundation_Establishment:
                human.append(avatar)
                
        heaven.sort(key=lambda a: get_base_strength(a), reverse=True)
        earth.sort(key=lambda a: get_base_strength(a), reverse=True)
        human.sort(key=lambda a: get_base_strength(a), reverse=True)
        
        lists_data = [
            ("heaven", heaven[:4], 10000),
            ("earth", earth[:4], 5000),
            ("human", human[:4], 2000)
        ]
        
        winners = {}
        story_candidates = []
        
        for list_name, participants, reward in lists_data:
            if len(participants) < 4:
                continue
                
            participant_names = ", ".join([a.name for a in participants])
            event_start = Event(
                world.month_stamp,
                t(f"tournament_start_{list_name}", participants=participant_names),
                related_avatars=[a.id for a in participants],
                is_major=True
            )
            events.append(event_start)
            
            # Semi-finals: 1 vs 4, 2 vs 3
            winner1, loser1, _, _ = decide_battle(participants[0], participants[3])
            winner2, loser2, _, _ = decide_battle(participants[1], participants[2])
            
            events.append(Event(
                world.month_stamp,
                t("tournament_battle_result", winner=winner1.name, loser=loser1.name),
                related_avatars=[winner1.id, loser1.id]
            ))
            events.append(Event(
                world.month_stamp,
                t("tournament_battle_result", winner=winner2.name, loser=loser2.name),
                related_avatars=[winner2.id, loser2.id]
            ))
            
            # Final: winner1 vs winner2
            final_winner, final_loser, _, _ = decide_battle(winner1, winner2)
            
            final_battle_event = Event(
                world.month_stamp,
                t("tournament_battle_result", winner=final_winner.name, loser=final_loser.name),
                related_avatars=[final_winner.id, final_loser.id]
            )
            events.append(final_battle_event)
            
            event_end = Event(
                world.month_stamp,
                t(f"tournament_end_{list_name}", winner=final_winner.name),
                related_avatars=[final_winner.id],
                is_major=True
            )
            events.append(event_end)
            
            # Reward
            final_winner.magic_stone += reward
            final_winner.temporary_effects.append({
                "source": f"tournament_{list_name}",
                "effects": {
                    "extra_respire_exp_multiplier": 0.5,
                    "extra_temper_exp_multiplier": 0.5,
                    "extra_epiphany_probability": 0.1,
                    "_desc": f"effect_tournament_{list_name}_first"
                },
                "start_month": int(world.month_stamp),
                "duration": 120
            })
            final_winner.recalc_effects()
            
            winners[list_name] = {
                "id": str(final_winner.id),
                "name": final_winner.name,
                "reward": reward
            }
            
            story_candidates.append({
                "list_name": list_name,
                "winner": final_winner,
                "loser": final_loser,
                "final_battle_event": final_battle_event,
                "end_event": event_end
            })

        if not hasattr(world.ranking_manager, "tournament_info"):
            world.ranking_manager.tournament_info = {
                "next_year": world.start_year + 1,
                "heaven_first": None,
                "earth_first": None,
                "human_first": None
            }

        world.ranking_manager.tournament_info["next_year"] = world.month_stamp.get_year() + 10
        world.ranking_manager.tournament_info["heaven_first"] = winners.get("heaven")
        world.ranking_manager.tournament_info["earth_first"] = winners.get("earth")
        world.ranking_manager.tournament_info["human_first"] = winners.get("human")
        
        # Story Generation
        if story_candidates:
            from src.classes.story_teller import StoryTeller
            
            for target in story_candidates:
                list_name_i18n = t(f"tournament_{target['list_name']}")
                gathering_info = t("Event Type: World Martial Arts Tournament\nScene Setting: The tournament is held to determine the strongest cultivators of the realm.")
                
                details_text = t("\n【Tournament Information】\n")
                details_text += t("List: {list_name}\n", list_name=list_name_i18n)
                details_text += t("Final Match: {winner} vs {loser}\n", winner=target["winner"].name, loser=target["loser"].name)
                details_text += t("Winner: {winner}\n", winner=target["winner"].name)
                
                details_text += t("\n【Finalists Information】\n")
                details_text += f"{target['winner'].name}:\n"
                details_text += f"{target['winner'].get_info(detailed=True)}\n\n"
                details_text += f"{target['loser'].name}:\n"
                details_text += f"{target['loser'].get_info(detailed=True)}\n\n"
                
                events_text = f"{target['final_battle_event'].content}\n{target['end_event'].content}"
                
                story = await StoryTeller.tell_gathering_story(
                    gathering_info=gathering_info,
                    events_text=events_text,
                    details_text=details_text,
                    related_avatars=[target["winner"], target["loser"]],
                    prompt=t(self.STORY_PROMPT_ID)
                )
                
                story_event = Event(
                    month_stamp=world.month_stamp,
                    content=story,
                    related_avatars=[target["winner"].id, target["loser"].id],
                    is_major=True 
                )
                events.append(story_event)
            
        if not events:
            events.append(Event(
                world.month_stamp,
                t("tournament_cancelled_due_to_insufficient_participants"),
                is_major=True
            ))
            
        return events
