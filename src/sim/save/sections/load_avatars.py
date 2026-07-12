from __future__ import annotations

from .base import LoadContext


class AvatarsLoadSection:
    key = "avatars"

    def load(self, context: LoadContext) -> None:
        from src.classes.core.avatar import Avatar
        from src.classes.relation.relation import RelationState
        from src.systems.world_secret import sync_public_world_secret_for_all

        world = context.world
        avatars_data = context.save_data.get("avatars", [])
        all_avatars = {}
        living_avatars = {}
        dead_avatars = {}
        for avatar_data in avatars_data:
            avatar = Avatar.from_save_dict(avatar_data, world)
            all_avatars[avatar.id] = avatar
            if avatar.is_dead:
                dead_avatars[avatar.id] = avatar
            else:
                living_avatars[avatar.id] = avatar
        context.all_avatars = all_avatars

        for avatar_data in avatars_data:
            avatar_id = avatar_data["id"]
            avatar = all_avatars[avatar_id]
            for other_id, relation_state_data in avatar_data.get("relations", {}).items():
                if other_id in all_avatars:
                    avatar.relations[all_avatars[other_id]] = RelationState.from_save_dict(relation_state_data)
            for other_id, relation_state_data in avatar_data.get("archived_relations", {}).items():
                if other_id in all_avatars:
                    avatar.archived_relations[all_avatars[other_id]] = RelationState.from_save_dict(relation_state_data)

        world.avatar_manager.avatars = living_avatars
        world.avatar_manager.dead_avatars = dead_avatars
        if getattr(world.world_secret, "public_revealed", False):
            sync_public_world_secret_for_all(world)
