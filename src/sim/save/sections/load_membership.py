from __future__ import annotations

from .base import LoadContext


class MembershipLoadSection:
    key = "membership"

    def load(self, context: LoadContext) -> None:
        from src.classes.technique import techniques_by_name

        world = context.world
        existed_sects = context.existed_sects or []
        all_avatars = context.all_avatars or {}

        for avatar in all_avatars.values():
            if avatar.sect:
                avatar.sect.add_member(avatar)

        for sect in existed_sects:
            if not sect.techniques and sect.technique_names:
                sect.techniques = [
                    techniques_by_name[t_name]
                    for t_name in sect.technique_names
                    if t_name in techniques_by_name
                ]

        world.existed_sects = existed_sects
        world.sect_context.from_existed_sects(existed_sects)
