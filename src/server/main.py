import sys
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 确保可以导入 src 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sim.simulator import Simulator
from src.classes.world import World
from src.classes.calendar import Month, Year, create_month_stamp
from src.run.create_map import create_cultivation_world_map, add_sect_headquarters
from src.sim.new_avatar import make_avatars as _new_make
from src.utils.config import CONFIG
from src.classes.sect import sects_by_id
import random

# 全局游戏实例
game_instance = {
    "world": None,
    "sim": None
}

def init_game():
    """初始化游戏世界，逻辑复用自 src/run/run.py"""
    print("正在初始化游戏世界...")
    game_map = create_cultivation_world_map()
    world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
    sim = Simulator(world)

    # 宗门初始化逻辑
    all_sects = list(sects_by_id.values())
    needed_sects = int(getattr(CONFIG.game, "sect_num", 0) or 0)
    
    # 简单的宗门抽样逻辑 (简化版)
    existed_sects = []
    if needed_sects > 0 and all_sects:
        pool = list(all_sects)
        random.shuffle(pool)
        existed_sects = pool[:needed_sects]

    if existed_sects:
        add_sect_headquarters(world.map, existed_sects)

    # 创建角色
    # 注意：这里直接调用 new_avatar 的 make_avatars，避免循环导入
    all_avatars = _new_make(world, count=CONFIG.game.init_npc_num, current_month_stamp=world.month_stamp, existed_sects=existed_sects)
    world.avatar_manager.avatars.update(all_avatars)
    
    game_instance["world"] = world
    game_instance["sim"] = sim
    print("游戏世界初始化完成！")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    init_game()
    yield
    # 关闭时清理（如果需要）

app = FastAPI(lifespan=lifespan)

# 允许跨域，方便前端开发
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "app": "Cultivation World Simulator Backend"}

@app.get("/api/state")
def get_state():
    """获取当前世界的一个快照（调试模式）"""
    try:
        # 1. 基础检查
        world = game_instance.get("world")
        if world is None:
             return {"step": 1, "error": "No world"}
        
        # 2. 时间检查
        y = 0
        m = 0
        try:
            y = int(world.month_stamp.get_year())
            m = int(world.month_stamp.get_month().value)
        except Exception as e:
            return {"step": 2, "error": str(e)}

        # 3. 角色列表检查
        av_list = []
        try:
            raw_avatars = list(world.avatar_manager.avatars.values())[:50] # 缩小范围
            for a in raw_avatars:
                # 极其保守的取值
                aid = str(getattr(a, "id", "no_id"))
                aname = str(getattr(a, "name", "no_name"))
                # 修正：使用 pos_x/pos_y
                ax = int(getattr(a, "pos_x", 0))
                ay = int(getattr(a, "pos_y", 0))
                aaction = "unknown"
                
                # 动作检查
                curr = getattr(a, "current_action", None)
                if curr:
                     act = getattr(curr, "action", None)
                     if act:
                         aaction = getattr(act, "name", "unnamed_action")
                     else:
                         aaction = str(curr)
                
                av_list.append({
                    "id": aid,
                    "name": aname,
                    "x": ax,
                    "y": ay,
                    "action": str(aaction)
                })
        except Exception as e:
            return {"step": 3, "error": str(e)}

        return {
            "status": "ok",
            "year": y,
            "month": m,
            "avatar_count": len(world.avatar_manager.avatars),
            "avatars": av_list
        }

    except Exception as e:
        return {"step": 0, "error": "Fatal: " + str(e)}

@app.post("/api/step")
async def step_world():
    """手动触发一帧（一个月）"""
    sim = game_instance["sim"]
    if not sim:
        return {"error": "Sim not initialized"}
    
    events = await sim.step()
    
    return {
        "message": "Step executed",
        "event_count": len(events),
        "events_sample": [str(e) for e in events[:5]]
    }

def start():
    """启动服务的入口函数"""
    # 改为 8002 端口
    uvicorn.run("src.server.main:app", host="0.0.0.0", port=8002, reload=False)

if __name__ == "__main__":
    start()
