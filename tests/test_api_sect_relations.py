import pytest
from fastapi.testclient import TestClient

from src.server import main
from src.sim.managers.sect_manager import SectManager
from src.classes.core.sect import Sect, SectHeadQuarter
from src.classes.alignment import Alignment
from src.systems.time import create_month_stamp, Year, Month
from src.classes.environment.map import Map


def _build_minimal_world_with_sects():
  """
  构造一个带有世界和两个宗门的最小环境，用于测试 /api/v1/query/sect-relations。
  仅验证接口结构和基本计算是否正常工作。
  """
  # 构造简单地图
  game_map = Map(width=5, height=5)
  month_stamp = create_month_stamp(Year(100), Month.JANUARY)

  from src.classes.core.world import World

  world = World(
    map=game_map,
    month_stamp=month_stamp,
  )

  # 构造两个宗门
  hq = SectHeadQuarter(name="HQ", desc="", image=None)  # type: ignore[arg-type]
  sect1 = Sect(
    id=1,
    name="SectA",
    desc="",
    member_act_style="",
    alignment=Alignment.RIGHTEOUS,
    headquarter=hq,
    technique_names=[],
    orthodoxy_id="dao",
  )
  sect2 = Sect(
    id=2,
    name="SectB",
    desc="",
    member_act_style="",
    alignment=Alignment.EVIL,
    headquarter=hq,
    technique_names=[],
    orthodoxy_id="dao",
  )

  world.existed_sects = [sect1, sect2]

  # 构造 SectManager 并挂到 sim 上
  from src.sim.simulator import Simulator

  sim = Simulator(world)
  sim.sect_manager = SectManager(world)

  return world, sim


@pytest.fixture
def api_client(monkeypatch):
  # 准备世界和模拟器
  world, sim = _build_minimal_world_with_sects()

  # 注入到全局 game_instance
  main.game_instance["world"] = world
  main.game_instance["sim"] = sim

  client = TestClient(main.app)
  return client


def test_get_sect_relations_basic(api_client: TestClient):
  """基本接口连通性与返回结构校验。"""
  resp = api_client.get("/api/v1/query/sect-relations")
  assert resp.status_code == 200

  data = resp.json()["data"]
  assert "relations" in data
  relations = data["relations"]
  assert isinstance(relations, list)

  # 只有两个宗门，应当只产生一条关系记录
  assert len(relations) <= 1
  if relations:
    rel = relations[0]
    assert rel["sect_a_id"] == 1
    assert rel["sect_b_id"] == 2
    assert isinstance(rel["value"], int)
    assert rel["diplomacy_status"] in {"war", "peace"}
    assert isinstance(rel["diplomacy_duration_months"], int)
    # reason_breakdown 为包含详细 delta/meta 的结构化原因列表
    assert isinstance(rel["reason_breakdown"], list)

