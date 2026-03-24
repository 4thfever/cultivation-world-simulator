import pytest

from src.classes.event import Event
from src.sim.simulator_engine.phases import social
from src.systems.time import Month


class TestEventLogic:
    @pytest.fixture
    def avatar_a(self, dummy_avatar):
        dummy_avatar.id = "avatar_a"
        dummy_avatar.name = "角色A"
        return dummy_avatar

    @pytest.fixture
    def avatar_b(self, base_world):
        from src.classes.core.avatar.core import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.systems.time import MonthStamp

        return Avatar(
            world=base_world,
            name="角色B",
            id="avatar_b",
            birth_month_stamp=MonthStamp(0),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.FEMALE,
            pos_x=0,
            pos_y=0,
            root=Root.WATER,
            personas=[],
            alignment=Alignment.RIGHTEOUS,
        )

    def test_process_interaction_from_event_is_noop(self, avatar_a, avatar_b):
        event = Event(
            month_stamp=avatar_a.world.month_stamp,
            content="A与B发生了互动",
            related_avatars=[avatar_a.id, avatar_b.id],
        )

        avatar_a.process_interaction_from_event(event)
        avatar_b.process_interaction_from_event(event)

        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 0
        assert avatar_b.relation_interaction_states[avatar_a.id]["count"] == 0

    def test_phase_handle_interactions_only_marks_processed_ids(self, base_world, avatar_a, avatar_b):
        base_world.avatar_manager.register_avatar(avatar_a)
        base_world.avatar_manager.register_avatar(avatar_b)

        processed_ids = set()
        event = Event(base_world.month_stamp, "事件1", related_avatars=[avatar_a.id, avatar_b.id])

        social.phase_handle_interactions(base_world.avatar_manager, [event], processed_ids)

        assert event.id in processed_ids
        assert avatar_a.relation_interaction_states[avatar_b.id]["count"] == 0

    @pytest.mark.asyncio
    async def test_phase_evolve_relations_now_only_normalizes_state(self, base_world, avatar_a, avatar_b):
        base_world.avatar_manager.register_avatar(avatar_a)
        base_world.avatar_manager.register_avatar(avatar_b)
        avatar_a.make_friend_with(avatar_b)

        events = await social.phase_evolve_relations(base_world.avatar_manager, [avatar_a, avatar_b])

        assert events == []
        assert avatar_a.get_friendliness(avatar_b) == 35
        assert avatar_b.get_friendliness(avatar_a) == 35

    def test_phase_update_calculated_relations_also_regresses_friendliness(self, base_world, avatar_a, avatar_b):
        from src.systems.time import Year, create_month_stamp

        base_world.month_stamp = create_month_stamp(Year(2), Month.JANUARY)
        avatar_a.make_friend_with(avatar_b)

        social.phase_update_calculated_relations(base_world, [avatar_a, avatar_b])

        assert avatar_a.get_friendliness(avatar_b) == 33
        assert avatar_b.get_friendliness(avatar_a) == 33
