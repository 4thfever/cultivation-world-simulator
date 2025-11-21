import sys
import os
import asyncio
import webbrowser
from contextlib import asynccontextmanager
from typing import List, Optional
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
from src.sim.save.save_game import save_game, list_saves
from src.sim.load.load_game import load_game
import random

# 全局游戏实例
game_instance = {
    "world": None,
    "sim": None,
    "is_paused": False # 新增暂停标记
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
            # 检查暂停状态
            if game_instance.get("is_paused", False):
                continue

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
    
    # 自动打开浏览器
    host = "127.0.0.1"
    port = 8002
    url = f"http://{host}:{port}"
    print(f"Ready! Opening browser at {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Failed to open browser: {e}")
        
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

# 路径处理：兼容开发环境和 PyInstaller 打包环境
if getattr(sys, 'frozen', False):
    # PyInstaller 打包模式
    base_path = sys._MEIPASS
    # 在 pack.ps1 中，我们把 web/dist 映射到了 web_dist
    WEB_DIST_PATH = os.path.join(base_path, 'web_dist')
    # assets 同理
    ASSETS_PATH = os.path.join(base_path, 'assets')
else:
    # 开发模式
    base_path = os.path.join(os.path.dirname(__file__), '..', '..')
    WEB_DIST_PATH = os.path.join(base_path, 'web', 'dist')
    ASSETS_PATH = os.path.join(base_path, 'assets')

# 1. 挂载游戏资源 (图片等)
if os.path.exists(ASSETS_PATH):
    app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")
else:
    print(f"Warning: Assets path not found: {ASSETS_PATH}")

# 2. 挂载前端静态页面 (Web Dist)
if os.path.exists(WEB_DIST_PATH):
    print(f"Serving Web UI from: {WEB_DIST_PATH}")
    app.mount("/", StaticFiles(directory=WEB_DIST_PATH, html=True), name="web_dist")
else:
    print(f"Warning: Web dist path not found: {WEB_DIST_PATH}. Please run 'npm run build' in web directory.")
    
    @app.get("/")
    def read_root():
        return {"status": "online", "app": "Cultivation World Simulator Backend (Headless / Dev Mode)"}

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
            "events": recent_events,
            "is_paused": game_instance.get("is_paused", False)
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

@app.post("/api/control/pause")
def pause_game():
    """暂停游戏循环"""
    game_instance["is_paused"] = True
    return {"status": "ok", "message": "Game paused"}

@app.post("/api/control/resume")
def resume_game():
    """恢复游戏循环"""
    game_instance["is_paused"] = False
    return {"status": "ok", "message": "Game resumed"}

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

# --- 存档系统 API ---

class SaveGameRequest(BaseModel):
    filename: Optional[str] = None

class LoadGameRequest(BaseModel):
    filename: str

@app.get("/api/saves")
def get_saves():
    """获取存档列表"""
    saves_list = list_saves()
    # 转换 Path 为 str，并整理格式
    result = []
    for path, meta in saves_list:
        result.append({
            "filename": path.name,
            "save_time": meta.get("save_time", ""),
            "game_time": meta.get("game_time", ""),
            "version": meta.get("version", "")
        })
    return {"saves": result}

@app.post("/api/game/save")
def api_save_game(req: SaveGameRequest):
    """保存游戏"""
    world = game_instance.get("world")
    sim = game_instance.get("sim")
    if not world or not sim:
        raise HTTPException(status_code=503, detail="Game not initialized")
    
    # 这里的 existed_sects 需要从 world 或者 sim 中获取，目前简单起见，
    # 我们可以遍历地图上的宗门总部，或者如果全局有保存最好。
    # 由于 init_game 只有一次，我们需要从 world 中反推 active sects
    # 但 save_game 签名里的 existed_sects 主要是为了记录 id。
    # 实际上 world.map.regions 中包含了宗门总部信息。
    # 或者更简单的：直接从 sects_by_id 取所有? 不太对。
    # 让我们看看 save_game 实现：它主要是存 id。
    # 我们可以传入空列表，如果在 load 时能容忍的话。
    # 实际上 load_game 里：existed_sects = [sects_by_id[sid] for sid in existed_sect_ids]
    # 所以 save 时如果不传，load 时就拿不到。
    # 临时方案：遍历所有宗门，如果它有领地或者有人，就算存在。
    # 或者更粗暴：CONFIG.game.sect_num 如果没变，可以不管。
    # 最好是 world 对象上能挂载 existed_sects。
    # 暂时方案：传入所有宗门作为 existed_sects (全集)，虽然有点浪费，但不丢数据。
    # 更好的方案：修改 init_game，把 existed_sects 挂载到 world 上。
    
    # 尝试从 world 属性获取（如果以后添加了）
    existed_sects = getattr(world, "existed_sects", [])
    if not existed_sects:
        # fallback: 所有 sects
        existed_sects = list(sects_by_id.values())

    success, filename = save_game(world, sim, existed_sects, save_path=None) # save_path=None 会自动生成时间戳文件名
    if success:
        return {"status": "ok", "filename": filename}
    else:
        raise HTTPException(status_code=500, detail="Save failed")

@app.post("/api/game/load")
def api_load_game(req: LoadGameRequest):
    """加载游戏"""
    # 安全检查：只允许加载 saves 目录下的文件
    if ".." in req.filename or "/" in req.filename or "\\" in req.filename:
         raise HTTPException(status_code=400, detail="Invalid filename")
    
    try:
        saves_dir = CONFIG.paths.saves
        target_path = saves_dir / req.filename
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # 加载
        new_world, new_sim, new_sects = load_game(target_path)
        
        # 确保挂载 existed_sects 以便下次保存
        new_world.existed_sects = new_sects

        # 替换全局实例
        game_instance["world"] = new_world
        game_instance["sim"] = new_sim
        
        return {"status": "ok", "message": "Game loaded"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Load failed: {str(e)}")

def start():
    """启动服务的入口函数"""
    # 改为 8002 端口
    # 使用 127.0.0.1 更加安全且避免防火墙弹窗
    # 注意：直接传递 app 对象而不是字符串，避免 PyInstaller 打包后找不到模块的问题
    uvicorn.run(app, host="127.0.0.1", port=8002)

if __name__ == "__main__":
    start()
