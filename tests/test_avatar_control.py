from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.server.services.avatar_control import delete_avatar_in_world


class RuntimeWithRoleplay(dict):
    def get_roleplay_session(self):
        return self["roleplay_session"]


def test_delete_avatar_rejects_controlled_roleplay_avatar():
    avatar = SimpleNamespace(id="avatar-1")
    avatar_manager = SimpleNamespace(
        avatars={"avatar-1": avatar},
        remove_avatar=lambda _avatar_id: pytest.fail("roleplay avatar must not be removed"),
    )
    runtime = RuntimeWithRoleplay(
        world=SimpleNamespace(avatar_manager=avatar_manager),
        roleplay_session={"controlled_avatar_id": "avatar-1"},
    )

    with pytest.raises(HTTPException) as exc_info:
        delete_avatar_in_world(runtime, avatar_id="avatar-1")

    assert exc_info.value.status_code == 409
