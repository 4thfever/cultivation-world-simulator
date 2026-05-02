from types import SimpleNamespace

from src.server.public_helpers import resolve_avatar_pic_id, scan_avatar_assets


def test_scan_avatar_assets_reads_realm_aware_avatar_tree(tmp_path):
    assets = tmp_path / "assets"
    (assets / "avatars" / "male" / "001").mkdir(parents=True)
    (assets / "avatars" / "male" / "001" / "qi_refining.png").write_bytes(b"png")
    (assets / "avatars" / "male" / "002").mkdir(parents=True)
    (assets / "avatars" / "male" / "002" / "foundation.png").write_bytes(b"png")
    (assets / "avatars" / "female" / "008").mkdir(parents=True)
    (assets / "avatars" / "female" / "008" / "qi_refining.png").write_bytes(b"png")

    assert scan_avatar_assets(assets_path=str(assets)) == {
        "males": [1],
        "females": [8],
    }


def test_resolve_avatar_pic_id_keeps_custom_index_semantics():
    avatar = SimpleNamespace(custom_pic_id=12, gender=SimpleNamespace(value="female"), id="a-1")

    assert resolve_avatar_pic_id(avatar_assets={"males": [1], "females": [8]}, avatar=avatar) == 12
