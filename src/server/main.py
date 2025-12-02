import sys
import os
import asyncio
import webbrowser
import subprocess
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
from src.run.load_map import load_cultivation_world_map
from src.sim.new_avatar import make_avatars as _new_make, create_avatar_from_request
from src.utils.config import CONFIG
from src.classes.sect import sects_by_id
from src.classes.technique import techniques_by_id
from src.classes.weapon import weapons_by_id
from src.classes.auxiliary import auxiliaries_by_id
from src.classes.appearance import get_appearance_by_level
from src.classes.persona import personas_by_id
from src.classes.cultivation import REALM_ORDER
from src.classes.alignment import Alignment
from src.classes.color import serialize_hover_lines
from src.classes.event import Event
from src.classes.celestial_phenomenon import celestial_phenomena_by_id
from src.classes.long_term_objective import set_user_long_term_objective, clear_user_long_term_objective
from src.sim.save.save_game import save_game, list_saves
from src.sim.load.load_game import load_game
import random

# 全局游戏实例
game_instance = {
    "world": None,
    "sim": None,
    "is_paused": True # 默认启动为暂停状态，等待前端连接唤醒
}

# Cache for avatar IDs
AVATAR_ASSETS = {
    "males": [],
    "females": []
}

def scan_avatar_assets():
    """Scan assets directory for avatar images"""
    global AVATAR_ASSETS
    
    def get_ids(subdir):
        directory = os.path.join(ASSETS_PATH, subdir)
        if not os.path.exists(directory):
            return []
        ids = []
        for f in os.listdir(directory):
            if f.lower().endswith('.png'):
                try:
                    name = os.path.splitext(f)[0]
                    ids.append(int(name))
                except ValueError:
                    pass
        return sorted(ids)

    AVATAR_ASSETS["males"] = get_ids("males")
    AVATAR_ASSETS["females"] = get_ids("females")
    print(f"Loaded avatar assets: {len(AVATAR_ASSETS['males'])} males, {len(AVATAR_ASSETS['females'])} females")

def get_avatar_pic_id(avatar_id: str, gender_val: str) -> int:
    """Deterministically get a valid pic_id for an avatar"""
    key = "females" if gender_val == "female" else "males"
    available = AVATAR_ASSETS.get(key, [])
    
    if not available:
        return 1
        
    # Use hash to pick an index from available IDs
    # Use abs() because hash can be negative
    idx = abs(hash(str(avatar_id))) % len(available)
    return available[idx]


def resolve_avatar_pic_id(avatar) -> int:
    """Return the actual avatar portrait ID, respecting custom overrides."""
    if avatar is None:
        return 1
    custom_pic_id = getattr(avatar, "custom_pic_id", None)
    if custom_pic_id is not None:
        return custom_pic_id
    gender_val = getattr(getattr(avatar, "gender", None), "value", "male")
    return get_avatar_pic_id(str(getattr(avatar, "id", "")), gender_val or "male")

# 触发配置重载的标记 (technique.csv updated)

# 简易的命令行参数检查 (不使用 argparse 以避免冲突和时序问题)
IS_DEV_MODE = "--dev" in sys.argv

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # 当第一个客户端连接时，自动恢复游戏
        if len(self.active_connections) == 1:
            self._set_pause_state(False, "检测到客户端连接，自动恢复游戏运行。")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        # 当最后一个客户端断开时，自动暂停游戏
        if len(self.active_connections) == 0:
            self._set_pause_state(True, "所有客户端已断开，自动暂停游戏以节省资源。")

    def _set_pause_state(self, should_pause: bool, log_msg: str):
        """辅助方法：切换暂停状态并打印日志"""
        if game_instance.get("is_paused") != should_pause:
            game_instance["is_paused"] = should_pause
            print(f"[Auto-Control] {log_msg}")

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
                month = month_obj.value
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

def serialize_phenomenon(phenomenon) -> Optional[dict]:
    """序列化天地灵机对象"""
    if not phenomenon:
        return None
    
    # 安全地获取 rarity.name
    rarity_str = "N"
    if hasattr(phenomenon, "rarity") and phenomenon.rarity:
        # 检查 rarity 是否是 Enum (RarityLevel)
        if hasattr(phenomenon.rarity, "name"):
            rarity_str = phenomenon.rarity.name
        # 检查 rarity 是否是 Rarity dataclass (包含 level 字段)
        elif hasattr(phenomenon.rarity, "level") and hasattr(phenomenon.rarity.level, "name"):
            rarity_str = phenomenon.rarity.level.name
            
    # 生成效果描述
    from src.utils.effect_desc import format_effects_to_text
    effect_desc = format_effects_to_text(phenomenon.effects) if hasattr(phenomenon, "effects") else ""

    return {
        "id": phenomenon.id,
        "name": phenomenon.name,
        "desc": phenomenon.desc,
        "rarity": rarity_str,
        "duration_years": phenomenon.duration_years,
        "effect_desc": effect_desc
    }

def init_game():
    """初始化游戏世界，逻辑复用自 src/run/run.py"""
    print("正在初始化游戏世界...")
    game_map = load_cultivation_world_map()
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
                
                # 找出新诞生的角色 ID 和 刚死亡的角色 ID
                newly_born_ids = set()
                newly_dead_ids = set()
                for e in events:
                    if "晋升为修士" in e.content and e.related_avatars:
                        newly_born_ids.update(e.related_avatars)
                    if ("身亡" in e.content or "老死" in e.content) and e.related_avatars:
                        newly_dead_ids.update(e.related_avatars)

                avatar_updates = []
                
                # 为了避免重复发送大量数据，我们区分处理：
                # - 新角色/刚死角色：发送完整数据（或关键状态更新）
                # - 旧角色：只发送位置 (x, y)（限制数量）
                
                # 1. 发送新角色的完整信息
                for aid in newly_born_ids:
                    a = world.avatar_manager.avatars.get(aid)
                    if a:
                        avatar_updates.append({
                            "id": str(a.id),
                            "name": a.name,
                            "x": int(getattr(a, "pos_x", 0)),
                            "y": int(getattr(a, "pos_y", 0)),
                            "gender": a.gender.value,
                            "pic_id": resolve_avatar_pic_id(a),
                            "action": getattr(a, "current_action", {}).get("name", "发呆") if hasattr(a, "current_action") and a.current_action else "发呆",
                            "is_dead": False
                        })

                # 2. 发送刚死角色的状态更新
                for aid in newly_dead_ids:
                    # 注意：死人可能不在 get_living_avatars() 里，但还在 avatars 里
                    a = world.avatar_manager.avatars.get(aid)
                    if a:
                        avatar_updates.append({
                            "id": str(a.id),
                            "name": a.name, # 名字也带上，防止前端没数据
                            "is_dead": True,
                            "action": "已故"
                        })

                # 3. 常规位置更新（暂时只发前 50 个旧角色，减少数据量）
                limit = 50
                count = 0
                # 只遍历活人更新位置
                for a in world.avatar_manager.get_living_avatars():
                    # 如果是新角色，已经在上面处理过了，跳过
                    if a.id in newly_born_ids:
                        continue
                        
                    if count < limit:
                        avatar_updates.append({
                            "id": str(a.id), 
                            "x": int(getattr(a, "pos_x", 0)), 
                            "y": int(getattr(a, "pos_y", 0))
                        })
                        count += 1

                # 构造广播数据包
                state = {
                    "type": "tick",
                    "year": int(world.month_stamp.get_year()),
                    "month": world.month_stamp.get_month().value,
                    "events": serialize_events_for_client(events),
                    "avatars": avatar_updates,
                    "phenomenon": serialize_phenomenon(world.current_phenomenon)
                }
                await manager.broadcast(state)
        except Exception as e:
            from src.run.log import get_logger
            print(f"Game loop error: {e}")
            get_logger().logger.error(f"Game loop error: {e}", exc_info=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    scan_avatar_assets()
    init_game()
    # 启动后台任务
    asyncio.create_task(game_loop())
    
    npm_process = None
    host = "127.0.0.1"
    
    if IS_DEV_MODE:
        print("🚀 启动开发模式 (Dev Mode)...")
        # 计算 web 目录 (假设在当前脚本的 ../../web)
        # 注意：这里直接重新计算路径，确保稳健
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        web_dir = os.path.join(project_root, 'web')
        
        print(f"正在启动前端开发服务 (npm run dev) 于: {web_dir}")
        # Windows 下使用 shell=True
        try:
            npm_process = subprocess.Popen(["npm", "run", "dev"], cwd=web_dir, shell=True)
            # 假设 Vite 默认端口是 5173
            target_url = "http://localhost:5173"
        except Exception as e:
            print(f"启动前端服务失败: {e}")
            target_url = f"http://{host}:8002"
    else:
        target_url = f"http://{host}:8002"
    
    # 自动打开浏览器
    print(f"Ready! Opening browser at {target_url}")
    try:
        webbrowser.open(target_url)
    except Exception as e:
        print(f"Failed to open browser: {e}")
        
    yield
    
    # 关闭时清理
    if npm_process:
        print("正在关闭前端开发服务...")
        try:
            # 尝试终止进程
            # Windows 下 terminate 可能无法杀死 shell=True 的子进程树，这里简单处理
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(npm_process.pid)])
        except Exception as e:
            print(f"关闭前端服务时出错: {e}")

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
    # 1. 获取 EXE 所在目录 (外部目录)
    exe_dir = os.path.dirname(sys.executable)
    
    # 2. 寻找外部的 web_static
    WEB_DIST_PATH = os.path.join(exe_dir, 'web_static')
    
    # 3. Assets 依然在 _internal 里 (因为我们在 pack.ps1 里用了 --add-data)
    # 注意：ASSETS_PATH 仍然指向 _internal/assets
    ASSETS_PATH = os.path.join(sys._MEIPASS, 'assets')
else:
    # 开发模式
    base_path = os.path.join(os.path.dirname(__file__), '..', '..')
    WEB_DIST_PATH = os.path.join(base_path, 'web', 'dist')
    ASSETS_PATH = os.path.join(base_path, 'assets')

# 规范化路径
WEB_DIST_PATH = os.path.abspath(WEB_DIST_PATH)
ASSETS_PATH = os.path.abspath(ASSETS_PATH)

print(f"Runtime mode: {'Frozen/Packaged' if getattr(sys, 'frozen', False) else 'Development'}")
print(f"Assets path: {ASSETS_PATH}")
print(f"Web dist path: {WEB_DIST_PATH}")

# (静态文件挂载已移动到文件末尾，以避免覆盖 API 路由)

# (read_root removed to allow StaticFiles to handle /)

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

@app.get("/api/meta/avatars")
def get_avatar_meta():
    return AVATAR_ASSETS


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
                    "pic_id": resolve_avatar_pic_id(a)
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
            "phenomenon": serialize_phenomenon(world.current_phenomenon),
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

@app.get("/api/detail")
def get_detail_info(
    target_type: str = Query(alias="type"),
    target_id: str = Query(alias="id")
):
    """获取结构化详情信息，替代/增强 hover info"""
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
    elif target_type == "sect":
        try:
            sid = int(target_id)
            target = sects_by_id.get(sid)
        except (ValueError, TypeError):
            target = None

    if target is None:
         raise HTTPException(status_code=404, detail="Target not found")
         
    if hasattr(target, "get_structured_info"):
        info = target.get_structured_info()
        return info
    else:
        # 回退到 hover info 如果没有结构化信息
        if hasattr(target, "get_hover_info"):
            lines = target.get_hover_info() or []
            return {
                "fallback": True,
                "name": getattr(target, "name", target_id),
                "lines": serialize_hover_lines([str(line) for line in lines])
            }
        return {"error": "No info available"}

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

# --- 角色管理 API ---

class CreateAvatarRequest(BaseModel):
    surname: Optional[str] = None
    given_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    level: Optional[int] = None
    sect_id: Optional[int] = None
    persona_ids: Optional[List[int]] = None
    pic_id: Optional[int] = None
    technique_id: Optional[int] = None
    weapon_id: Optional[int] = None
    auxiliary_id: Optional[int] = None
    alignment: Optional[str] = None
    appearance: Optional[int] = None
    relations: Optional[List[dict]] = None

class DeleteAvatarRequest(BaseModel):
    avatar_id: str

@app.get("/api/meta/game_data")
def get_game_data():
    """获取游戏元数据（宗门、个性、境界等），供前端选择"""
    # 1. 宗门列表
    sects_list = []
    for s in sects_by_id.values():
        sects_list.append({
            "id": s.id,
            "name": s.name,
            "alignment": s.alignment.value
        })
    
    # 2. 个性列表
    personas_list = []
    for p in personas_by_id.values():
        personas_list.append({
            "id": p.id,
            "name": p.name,
            "desc": p.desc,
            "rarity": p.rarity.level.name if hasattr(p.rarity, 'level') else "N"
        })
        
    # 3. 境界列表
    realms_list = [r.value for r in REALM_ORDER]

    # 4. 功法 / 兵器 / 辅助装备
    techniques_list = [
        {
            "id": t.id,
            "name": t.name,
            "grade": t.grade.value,
            "attribute": t.attribute.value,
            "sect": t.sect
        }
        for t in techniques_by_id.values()
    ]

    weapons_list = [
        {
            "id": w.id,
            "name": w.name,
            "type": w.weapon_type.value,
            "grade": w.grade.value,
            "sect_id": w.sect_id
        }
        for w in weapons_by_id.values()
    ]

    auxiliaries_list = [
        {
            "id": a.id,
            "name": a.name,
            "grade": a.grade.value,
            "sect_id": a.sect_id
        }
        for a in auxiliaries_by_id.values()
    ]
    
    alignments_list = [
        {
            "value": align.value,
            "label": str(align)
        }
        for align in Alignment
    ]

    return {
        "sects": sects_list,
        "personas": personas_list,
        "realms": realms_list,
        "techniques": techniques_list,
        "weapons": weapons_list,
        "auxiliaries": auxiliaries_list,
        "alignments": alignments_list
    }

@app.get("/api/meta/avatar_list")
def get_avatar_list_simple():
    """获取简略的角色列表，用于管理界面"""
    world = game_instance.get("world")
    if not world:
        return {"avatars": []}
    
    result = []
    for a in world.avatar_manager.avatars.values():
        sect_name = a.sect.name if a.sect else "散修"
        realm_str = a.cultivation_progress.realm.value if hasattr(a, 'cultivation_progress') else "未知"
        
        result.append({
            "id": str(a.id),
            "name": a.name,
            "sect_name": sect_name,
            "realm": realm_str,
            "gender": a.gender.value,
            "age": a.age.age
        })
    
    # 按名字排序
    result.sort(key=lambda x: x["name"])
    return {"avatars": result}

@app.get("/api/meta/phenomena")
def get_phenomena_list():
    """获取所有可选的天地灵机列表"""
    result = []
    # 按 ID 排序
    for p in sorted(celestial_phenomena_by_id.values(), key=lambda x: x.id):
        result.append(serialize_phenomenon(p))
    return {"phenomena": result}

class SetPhenomenonRequest(BaseModel):
    id: int

@app.post("/api/control/set_phenomenon")
def set_phenomenon(req: SetPhenomenonRequest):
    world = game_instance.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
    
    p = celestial_phenomena_by_id.get(req.id)
    if not p:
        raise HTTPException(status_code=404, detail="Phenomenon not found")
        
    world.current_phenomenon = p
    
    # 重置计时器，使其从当前年份开始重新计算持续时间
    try:
        current_year = int(world.month_stamp.get_year())
        world.phenomenon_start_year = current_year
    except Exception:
        pass
    
    return {"status": "ok", "message": f"Phenomenon set to {p.name}"}

@app.post("/api/action/create_avatar")
def create_avatar(req: CreateAvatarRequest):
    """创建新角色"""
    world = game_instance.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
        
    try:
        # 准备参数
        sect = None
        if req.sect_id is not None:
            sect = sects_by_id.get(req.sect_id)
            
        personas = None
        if req.persona_ids:
            personas = req.persona_ids # create_avatar_from_request 支持 int 列表

        have_name = False
        final_name = None
        surname = (req.surname or "").strip()
        given_name = (req.given_name or "").strip()
        if surname or given_name:
            if surname and given_name:
                final_name = f"{surname}{given_name}"
                have_name = True
            elif surname:
                final_name = f"{surname}某"
                have_name = True
            else:
                final_name = given_name
                have_name = True
        if not have_name:
            final_name = None

        # 创建角色
        # 注意：level 如果是境界枚举值对应的等级范围，前端可能传的是 realm index，后端需要转换吗？
        # 简单起见，我们假设 level 传的是具体等级 (1-120) 或者 realm index * 30 + 1
        # create_avatar_from_request 接收 level (int)
        
        avatar = create_avatar_from_request(
            world,
            world.month_stamp,
            name=final_name,
            gender=req.gender, # "男"/"女"
            age=req.age,
            level=req.level,
            sect=sect,
            personas=personas,
            technique=req.technique_id,
            weapon=req.weapon_id,
            auxiliary=req.auxiliary_id,
            appearance=req.appearance,
            relations=req.relations
        )

        if req.pic_id is not None:
            gender_key = "females" if getattr(avatar.gender, "value", "male") == "female" else "males"
            available_ids = set(AVATAR_ASSETS.get(gender_key, []))
            if available_ids and req.pic_id not in available_ids:
                raise HTTPException(status_code=400, detail="Invalid pic_id for selected gender")
            avatar.custom_pic_id = req.pic_id

        if req.alignment:
            avatar.alignment = Alignment.from_str(req.alignment)

        if req.appearance is not None:
            avatar.appearance = get_appearance_by_level(req.appearance)

        # 关系已经在 create_avatar_from_request 中根据参数设置好了，
        # 且该函数内部调用 MortalPlanner 时已经指定 allow_relations=False，不会生成随机关系。
        # 因此这里不需要再清空关系，否则会把自己选的关系删掉。

        if req.alignment:
            avatar.alignment = Alignment.from_str(req.alignment)

        # 注册到管理器
        world.avatar_manager.avatars[avatar.id] = avatar
        
        return {
            "status": "ok", 
            "message": f"Created avatar {avatar.name}",
            "avatar_id": str(avatar.id)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/action/delete_avatar")
def delete_avatar(req: DeleteAvatarRequest):
    """删除角色"""
    world = game_instance.get("world")
    if not world:
        raise HTTPException(status_code=503, detail="World not initialized")
    
    if req.avatar_id not in world.avatar_manager.avatars:
        raise HTTPException(status_code=404, detail="Avatar not found")
        
    try:
        world.avatar_manager.remove_avatar(req.avatar_id)
        return {"status": "ok", "message": "Avatar deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

# --- 静态文件挂载 (必须放在最后) ---

# 1. 挂载游戏资源 (图片等)
if os.path.exists(ASSETS_PATH):
    app.mount("/assets", StaticFiles(directory=ASSETS_PATH), name="assets")
else:
    print(f"Warning: Assets path not found: {ASSETS_PATH}")

# 2. 挂载前端静态页面 (Web Dist)
# 放在最后，因为 "/" 会匹配所有未定义的路由
# 仅在非开发模式下挂载，避免覆盖开发服务器
if not IS_DEV_MODE:
    if os.path.exists(WEB_DIST_PATH):
        print(f"Serving Web UI from: {WEB_DIST_PATH}")
        app.mount("/", StaticFiles(directory=WEB_DIST_PATH, html=True), name="web_dist")
    else:
        print(f"Warning: Web dist path not found: {WEB_DIST_PATH}.")
else:
    print("Dev Mode: Skipping static file mount for '/' (using Vite dev server instead)")

def start():
    """启动服务的入口函数"""
    # 改为 8002 端口
    # 使用 127.0.0.1 更加安全且避免防火墙弹窗
    # 注意：直接传递 app 对象而不是字符串，避免 PyInstaller 打包后找不到模块的问题
    uvicorn.run(app, host="127.0.0.1", port=8002)

if __name__ == "__main__":
    start()
