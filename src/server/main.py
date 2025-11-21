import sys
import os
import asyncio
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel

# 确保可以导入 src 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sim.simulator import Simulator
from src.classes.world import World
from src.classes.calendar import Month, Year, create_month_stamp
from src.run.create_map import create_cultivation_world_map, add_sect_headquarters
from src.sim.new_avatar import make_avatars as _new_make
from src.utils.config import CONFIG
from src.classes.sect import sects_by_id
from src.classes.color import serialize_hover_lines
from src.classes.event import Event
from src.classes.long_term_objective import set_user_long_term_objective, clear_user_long_term_objective
import random

# 全局游戏实例
game_instance = {
    "world": None,
    "sim": None
}

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        import json
        try:
            # 简单序列化，实际生产可能需要更复杂的 Encoder
            txt = json.dumps(message, default=str)
            for connection in self.active_connections:
                await connection.send_text(txt)
        except Exception as e:
            print(f"Broadcast error: {e}")

manager = ConnectionManager()


def serialize_events_for_client(events: List[Event]) -> List[dict]:
    """将事件转换为前端可用的结构。"""
    serialized: List[dict] = []
    for idx, event in enumerate(events):
        month_stamp = getattr(event, "month_stamp", None)
        stamp_int = None
        year = None
        month = None
        if month_stamp is not None:
            try:
                stamp_int = int(month_stamp)
            except Exception:
                stamp_int = None
            try:
                year = int(month_stamp.get_year())
            except Exception:
                year = None
            try:
                month_obj = month_stamp.get_month()
            except Exception:
                month = None

        related_raw = getattr(event, "related_avatars", None) or []
        related_ids = [str(a) for a in related_raw if a is not None]

        serialized.append({
            "id": getattr(event, "event_id", None) or f"{stamp_int or 'evt'}-{idx}",
            "text": str(event),
            "content": getattr(event, "content", ""),
            "year": year,
            "month": month,
            "month_stamp": stamp_int,
            "related_avatar_ids": related_ids,
            "is_major": bool(getattr(event, "is_major", False)),
            "is_story": bool(getattr(event, "is_story", False)),
        })
    return serialized

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

async def game_loop():
    """后台自动运行游戏循环"""
    print("后台游戏循环已启动...")
    while True:
        # 控制游戏速度，例如每秒 1 次更新
        await asyncio.sleep(1.0) 
        
        try:
            sim = game_instance.get("sim")
            world = game_instance.get("world")
            
            if sim and world:
                # 执行一步
                events = await sim.step()
                
                # 构造广播数据包
                state = {
                    "type": "tick",
                    "year": int(world.month_stamp.get_year()),
                    "month": world.month_stamp.get_month().value,
                    "events": serialize_events_for_client(events),
                    # 暂时只发前 50 个角色的位置更新，减少数据量
                    "avatars": [
                        {
                            "id": str(a.id), 
                            "x": int(getattr(a, "pos_x", 0)), 
                            "y": int(getattr(a, "pos_y", 0))
                        } 
                        for a in list(world.avatar_manager.avatars.values())[:50]
                    ]
                }
                await manager.broadcast(state)
        except Exception as e:
            print(f"Game loop error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    init_game()
    # 启动后台任务
    asyncio.create_task(game_loop())
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

# 挂载静态资源
ASSETS_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')
if os.path.exists(ASSETS_PATH):
    app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")
else:
    print(f"Warning: Assets path not found: {ASSETS_PATH}")

@app.get("/")
def read_root():
    return {"status": "online", "app": "Cultivation World Simulator Backend"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接活跃，接收客户端指令（目前暂不处理复杂指令）
            data = await websocket.receive_text()
            # echo test
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(websocket)

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
                    "action": str(aaction),
                    "gender": str(a.gender.value),
                    "pic_id": (hash(a.id) % 15) + 1
                })
        except Exception as e:
            return {"step": 3, "error": str(e)}

        recent_events = []
        try:
            event_manager = getattr(world, "event_manager", None)
            if event_manager:
                recent_events = serialize_events_for_client(event_manager.get_recent_events(limit=50))
        except Exception:
            recent_events = []

        return {
            "status": "ok",
            "year": y,
            "month": m,
            "avatar_count": len(world.avatar_manager.avatars),
            "avatars": av_list,
            "events": recent_events
        }

    except Exception as e:
        return {"step": 0, "error": "Fatal: " + str(e)}

@app.get("/api/map")
def get_map():
    """获取静态地图数据（仅需加载一次）"""
    world = game_instance.get("world")
    if not world or not world.map:
        return {"error": "No map"}
    
    # 构造二维数组
    w, h = world.map.width, world.map.height
    map_data = []
    for y in range(h):
        row = []
        for x in range(w):
            tile = world.map.get_tile(x, y)
            row.append(tile.type.name)
        map_data.append(row)
        
    # 构造区域列表
    regions_data = []
    if world.map and hasattr(world.map, 'regions'):
        for r in world.map.regions.values():
            # 确保有中心点
            if hasattr(r, 'center_loc') and r.center_loc:
                rtype = "unknown"
                if hasattr(r, 'get_region_type'):
                    rtype = r.get_region_type()
                
                region_dict = {
                    "id": r.id,
                    "name": r.name,
                    "type": rtype,
                    "x": r.center_loc[0],
                    "y": r.center_loc[1]
                }
                # 如果是宗门区域，额外传递 sect_name 用于前端加载图片
                if hasattr(r, 'sect_name'):
                    region_dict["sect_name"] = r.sect_name
                
                regions_data.append(region_dict)
        
    return {
        "width": w,
        "height": h,
        "data": map_data,
        "regions": regions_data
    }

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

@app.get("/api/hover")
def get_hover_info(
    target_type: str = Query(alias="type"),
    target_id: str = Query(alias="id")
):
    world = game_instance.get("world")
    if world is None:
        raise HTTPException(status_code=503, detail="World not initialized")

    target = None
    if target_type == "avatar":
        target = world.avatar_manager.avatars.get(target_id)
    elif target_type == "region":
        if world.map and hasattr(world.map, "regions"):
            regions = world.map.regions
            target = regions.get(target_id)
            if target is None:
                try:
                    target = regions.get(int(target_id))
                except (ValueError, TypeError):
                    target = None
    else:
        raise HTTPException(status_code=400, detail="Unsupported target type")

    if target is None:
        raise HTTPException(status_code=404, detail="Target not found")
    if not hasattr(target, "get_hover_info"):
        raise HTTPException(status_code=422, detail="Target has no hover info")

    lines = target.get_hover_info() or []
    return {
        "id": target_id,
        "type": target_type,
        "name": getattr(target, "name", target_id),
        "lines": serialize_hover_lines([str(line) for line in lines]),
    }

class SetObjectiveRequest(BaseModel):
    avatar_id: str
    content: str

class ClearObjectiveRequest(BaseModel):
    avatar_id: str

@app.post("/api/action/set_long_term_objective")
def set_long_term_objective(req: SetObjectiveRequest):
    world = game_instance.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
    
    avatar = world.avatar_manager.avatars.get(req.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
        
    set_user_long_term_objective(avatar, req.content)
    return {"status": "ok", "message": "Objective set"}

@app.post("/api/action/clear_long_term_objective")
def clear_long_term_objective(req: ClearObjectiveRequest):
    world = game_instance.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
        
    avatar = world.avatar_manager.avatars.get(req.avatar_id)
    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")
        
    cleared = clear_user_long_term_objective(avatar)
    return {
        "status": "ok", 
        "message": "Objective cleared" if cleared else "No user objective to clear"
    }

def start():
    """启动服务的入口函数"""
    # 改为 8002 端口
    uvicorn.run("src.server.main:app", host="0.0.0.0", port=8002, reload=False)

if __name__ == "__main__":
    start()
