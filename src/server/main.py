import sys
import os

# ==============================================================================
# 修复 PyInstaller 打包并在非中文 Windows (如英语环境) 运行时 print 导致的崩溃问题。
# 系统默认可能回退至 cp1252 编码，此时如果 print 包含中文字符的路径就会抛出 UnicodeEncodeError。
# 我们在此强制将标准输出/错误流重置为 UTF-8，并将无法转换的字符替换掉，以防报错崩溃。
# ==============================================================================
for stream_name in ('stdout', 'stderr'):
    stream = getattr(sys, stream_name, None)
    if stream is not None:
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
# ==============================================================================

import asyncio
import webview  # type: ignore
import subprocess
import time
import threading
import signal
import random
import re
import logging
from omegaconf import OmegaConf
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
from src.classes.core.world import World
from src.classes.history import HistoryManager
from src.systems.time import Month, Year, create_month_stamp
from src.run.load_map import load_cultivation_world_map
from src.sim.avatar_init import make_avatars as _new_make_random, create_avatar_from_request
from src.utils.config import CONFIG, load_config
from src.classes.core.sect import sects_by_id
from src.classes.technique import techniques_by_id
from src.classes.items.weapon import weapons_by_id
from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.appearance import get_appearance_by_level
from src.classes.persona import personas_by_id
from src.systems.cultivation import REALM_ORDER
from src.classes.alignment import Alignment
from src.classes.event import Event
from src.classes.celestial_phenomenon import celestial_phenomena_by_id
from src.classes.long_term_objective import set_user_long_term_objective, clear_user_long_term_objective
from src.sim import save_game, list_saves, load_game, get_events_db_path, check_save_compatibility
from src.utils.llm.client import test_connectivity
from src.utils.llm.config import LLMConfig, LLMMode
from src.run.data_loader import reload_all_static_data
from src.classes.language import language_manager, LanguageType

# 全局游戏实例
game_instance = {
    "world": None,
    "sim": None,
    "is_paused": True,  # 默认启动为暂停状态，等待前端连接唤醒
    # 初始化状态字段
    "init_status": "idle",  # idle | pending | in_progress | ready | error
    "init_phase": 0,         # 当前阶段 (0-5)
    "init_phase_name": "",   # 当前阶段名称
    "init_progress": 0,      # 总体进度 (0-100)
    "init_error": None,      # 错误信息
    "init_start_time": None, # 初始化开始时间戳
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

def resolve_avatar_action_emoji(avatar) -> str:
    """获取角色当前动作的 Emoji"""
    if not avatar:
        return ""
    curr = getattr(avatar, "current_action", None)
    if not curr:
        return ""
    
    # ActionInstance.action -> Action 实例
    act_instance = getattr(curr, "action", None)
    if not act_instance:
        return ""

    return getattr(act_instance, "EMOJI", "")

# 触发配置重载的标记 (technique.csv updated)

# 简易的命令行参数检查 (不使用 argparse 以避免冲突和时序问题)
IS_DEV_MODE = "--dev" in sys.argv

class EndpointFilter(logging.Filter):
    """
    Log filter to hide successful /api/init-status requests (polling)
    to reduce console noise.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /api/init-status") == -1

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # 不再自动恢复游戏，让用户明确选择"新游戏"或"加载存档"。
        # 这样可以避免在用户加载存档前就生成初始化事件。
        if len(self.active_connections) == 1:
            print("[Auto-Control] 检测到客户端连接，游戏保持暂停状态，等待用户操作。")

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


def serialize_active_domains(world: World) -> List[dict]:
    """序列化所有秘境列表（包括开启和未开启的）"""
    domains_data = []
    if not world or not world.gathering_manager:
        return []
    
    # 找到 HiddenDomain 实例
    hidden_domain_gathering = None
    for gathering in world.gathering_manager.gatherings:
        if gathering.__class__.__name__ == "HiddenDomain":
            hidden_domain_gathering = gathering
            break
            
    if hidden_domain_gathering:
        # 获取所有配置（假设 _load_configs 开销不大，或者已缓存）
        # 这里为了确保获取最新状态，重新加载配置
        # 注意：访问受保护方法 _load_configs
        all_configs = hidden_domain_gathering._load_configs()
        
        # 获取当前开启的 ID 集合
        active_ids = {d.id for d in hidden_domain_gathering._active_domains}
        
        for d in all_configs:
            is_open = d.id in active_ids
            
            domains_data.append({
                "id": d.id,
                "name": d.name,
                "desc": d.desc,
                "required_realm": str(d.required_realm), 
                "danger_prob": d.danger_prob,
                "drop_prob": d.drop_prob,
                "is_open": is_open,
                "cd_years": d.cd_years,
                "open_prob": d.open_prob
            })
            
    return domains_data

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
            "id": getattr(event, "id", None) or f"{stamp_int or 'evt'}-{idx}",
            "text": str(event),
            "content": getattr(event, "content", ""),
            "year": year,
            "month": month,
            "month_stamp": stamp_int,
            "related_avatar_ids": related_ids,
            "is_major": bool(getattr(event, "is_major", False)),
            "is_story": bool(getattr(event, "is_story", False)),
            "created_at": getattr(event, "created_at", 0.0),
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
    from src.classes.effect import format_effects_to_text
    effect_desc = format_effects_to_text(phenomenon.effects) if hasattr(phenomenon, "effects") else ""

    return {
        "id": phenomenon.id,
        "name": phenomenon.name,
        "desc": phenomenon.desc,
        "rarity": rarity_str,
        "duration_years": phenomenon.duration_years,
        "effect_desc": effect_desc
    }

def check_llm_connectivity() -> tuple[bool, str]:
    """
    检查 LLM 连通性
    
    Returns:
        (是否成功, 错误信息)
    """
    try:
        from src.utils.llm.config import LLMMode, LLMConfig
        
        normal_config = LLMConfig.from_mode(LLMMode.NORMAL)
        fast_config = LLMConfig.from_mode(LLMMode.FAST)
        
        # 检查配置是否完整
        if not normal_config.api_key or not normal_config.base_url:
            return False, "LLM 配置不完整：请填写 API Key 和 Base URL"
        
        if not normal_config.model_name:
            return False, "LLM 配置不完整：请填写智能模型名称"
        
        # 判断是否需要测试两次
        same_model = (normal_config.model_name == fast_config.model_name and 
                     normal_config.base_url == fast_config.base_url and
                     normal_config.api_key == fast_config.api_key)
        
        if same_model:
            # 只测试一次
            print(f"检测 LLM 连通性（单模型）: {normal_config.model_name}")
            success, error = test_connectivity(LLMMode.NORMAL, normal_config)
            if not success:
                return False, f"连接失败：{error}"
        else:
            # 测试两次
            print(f"检测智能模型连通性: {normal_config.model_name}")
            success, error = test_connectivity(LLMMode.NORMAL, normal_config)
            if not success:
                return False, f"智能模型连接失败：{error}"
            
            print(f"检测快速模型连通性: {fast_config.model_name}")
            success, error = test_connectivity(LLMMode.FAST, fast_config)
            if not success:
                return False, f"快速模型连接失败：{error}"
        
        return True, ""
        
    except Exception as e:
        return False, f"连通性检测异常：{str(e)}"

# 初始化阶段名称映射（用于前端显示）
INIT_PHASE_NAMES = {
    0: "scanning_assets",
    1: "loading_map",
    2: "processing_history",
    3: "initializing_sects",
    4: "generating_avatars",
    5: "checking_llm",
    6: "generating_initial_events",
}

def update_init_progress(phase: int, phase_name: str = ""):
    """更新初始化进度。"""
    game_instance["init_phase"] = phase
    game_instance["init_phase_name"] = phase_name or INIT_PHASE_NAMES.get(phase, "")
    # 最后一阶段到 100%
    progress_map = {0: 0, 1: 10, 2: 25, 3: 40, 4: 55, 5: 70, 6: 85}
    game_instance["init_progress"] = progress_map.get(phase, phase * 14)
    print(f"[Init] Phase {phase}: {game_instance['init_phase_name']} ({game_instance['init_progress']}%)")

async def init_game_async():
    """异步初始化游戏世界，带进度更新。"""
    game_instance["init_status"] = "in_progress"
    game_instance["init_start_time"] = time.time()
    game_instance["init_error"] = None

    try:
        # 阶段 0: 资源扫描
        update_init_progress(0, "scanning_assets")
        
        # === 重置所有静态数据，清除历史修改污染 ===
        print("正在重置世界规则数据...")
        reload_all_static_data()
        
        await asyncio.to_thread(scan_avatar_assets)

        # 阶段 1: 地图加载
        update_init_progress(1, "loading_map")
        game_map = await asyncio.to_thread(load_cultivation_world_map)

        # 初始化 SQLite 事件数据库
        from datetime import datetime
        from src.sim import get_events_db_path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        save_name = f"save_{timestamp}"
        saves_dir = CONFIG.paths.saves
        saves_dir.mkdir(parents=True, exist_ok=True)
        save_path = saves_dir / f"{save_name}.json"
        events_db_path = get_events_db_path(save_path)
        
        game_instance["current_save_path"] = save_path
        print(f"事件数据库: {events_db_path}")

        start_year = getattr(CONFIG.game, "start_year", 100)
        world = World.create_with_db(
            map=game_map,
            month_stamp=create_month_stamp(Year(start_year), Month.JANUARY),
            events_db_path=events_db_path,
            start_year=start_year,
        )
        sim = Simulator(world)

        # 阶段 2: 历史背景影响 (如果配置了历史)
        update_init_progress(2, "processing_history")
        world_history = getattr(CONFIG.game, "world_history", "")
        if world_history and world_history.strip():
            world.set_history(world_history)
            print(f"正在根据历史背景重塑世界: {world_history[:50]}...")
            try:
                history_mgr = HistoryManager(world)
                await history_mgr.apply_history_influence(world_history)
                print("历史背景应用完成")
            except Exception as e:
                print(f"[警告] 历史背景应用失败: {e}")
        
        # 阶段 3: 宗门初始化
        update_init_progress(3, "initializing_sects")
        all_sects = list(sects_by_id.values())
        needed_sects = int(getattr(CONFIG.game, "sect_num", 0) or 0)
        existed_sects = []
        if needed_sects > 0 and all_sects:
            pool = list(all_sects)
            random.shuffle(pool)
            existed_sects = pool[:needed_sects]

        # 阶段 4: 角色生成
        update_init_progress(4, "generating_avatars")
        target_total_count = int(getattr(CONFIG.game, "init_npc_num", 12))
        final_avatars = {}

        if target_total_count > 0:
            def _make_random_sync():
                return _new_make_random(
                    world,
                    count=target_total_count,
                    current_month_stamp=world.month_stamp,
                    existed_sects=existed_sects
                )
            random_avatars = await asyncio.to_thread(_make_random_sync)
            final_avatars.update(random_avatars)
            print(f"生成了 {len(random_avatars)} 位随机路人")

        world.avatar_manager.avatars.update(final_avatars)
        game_instance["world"] = world
        game_instance["sim"] = sim

        # 阶段 5: LLM 连通性检测
        update_init_progress(5, "checking_llm")
        print("正在检测 LLM 连通性...")
        # 使用线程池执行，避免阻塞事件循环，让 /api/init-status 可以响应
        success, error_msg = await asyncio.to_thread(check_llm_connectivity)

        if not success:
            print(f"[警告] LLM 连通性检测失败: {error_msg}")
            game_instance["llm_check_failed"] = True
            game_instance["llm_error_message"] = error_msg
        else:
            print("LLM 连通性检测通过")
            game_instance["llm_check_failed"] = False
            game_instance["llm_error_message"] = ""

        # 阶段 6: 生成初始事件（第一次 sim.step）
        update_init_progress(6, "generating_initial_events")
        print("正在生成初始事件...")
        
        # 取消暂停，执行第一步来生成初始事件
        game_instance["is_paused"] = False
        try:
            await sim.step()
            print("初始事件生成完成")
        except Exception as e:
            print(f"[警告] 初始事件生成失败: {e}")
        finally:
            # 执行完后重新暂停，等待前端准备好
            game_instance["is_paused"] = True

        # 完成
        game_instance["init_status"] = "ready"
        game_instance["init_progress"] = 100
        print("游戏世界初始化完成！")

    except Exception as e:
        import traceback
        traceback.print_exc()
        game_instance["init_status"] = "error"
        game_instance["init_error"] = str(e)
        print(f"[Error] 初始化失败: {e}")



async def game_loop():
    """后台自动运行游戏循环。"""
    print("后台游戏循环已启动，等待初始化完成...")
    
    # 等待初始化完成
    while game_instance.get("init_status") not in ("ready", "error"):
        await asyncio.sleep(0.5)
    
    if game_instance.get("init_status") == "error":
        print("[game_loop] 初始化失败，游戏循环退出。")
        return
    
    print("[game_loop] 初始化完成，开始游戏循环。")
    
    while True:
        # 控制游戏速度，例如每秒 1 次更新
        await asyncio.sleep(1.0)
        
        try:
            # 检查暂停状态
            if game_instance.get("is_paused", False):
                continue
            
            # 再次检查初始化状态（可能被重新初始化）
            if game_instance.get("init_status") != "ready":
                continue

            sim = game_instance.get("sim")
            world = game_instance.get("world")
            
            if sim and world:
                # 执行一步
                events = await sim.step()
                
                # 获取状态变更 (Source of Truth: AvatarManager)
                newly_born_ids = world.avatar_manager.pop_newly_born()
                newly_dead_ids = world.avatar_manager.pop_newly_dead()

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
                            "action": a.current_action_name,
                            "action_emoji": resolve_avatar_action_emoji(a),
                            "is_dead": False
                        })

                # 2. 发送刚死角色的状态更新
                for aid in newly_dead_ids:
                    # 使用 get_avatar 以兼容死者查询
                    a = world.avatar_manager.get_avatar(aid)
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
                            "y": int(getattr(a, "pos_y", 0)),
                            "action_emoji": resolve_avatar_action_emoji(a)
                        })
                        count += 1

                # 构造广播数据包
                state = {
                    "type": "tick",
                    "year": int(world.month_stamp.get_year()),
                    "month": world.month_stamp.get_month().value,
                    "events": serialize_events_for_client(events),
                    "avatars": avatar_updates,
                    "phenomenon": serialize_phenomenon(world.current_phenomenon),
                    "active_domains": serialize_active_domains(world)
                }
                await manager.broadcast(state)
        except Exception as e:
            from src.run.log import get_logger
            print(f"Game loop error: {e}")
            get_logger().logger.error(f"Game loop error: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Filter out health check / polling logs
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

    # 初始化语言设置
    from src.utils.config import update_paths_for_language
    from src.utils.df import reload_game_configs
    
    system_conf = getattr(CONFIG, "system", None)
    if system_conf:
        # OmegaConf 对象支持 get 或者 . 访问，这里用 getattr 安全一点
        lang_code = getattr(system_conf, "language", "zh-CN")
        language_manager.set_language(str(lang_code))
    else:
        language_manager.set_language("zh-CN")
    
    # 根据语言初始化路径
    update_paths_for_language()
    # 路径更新后，必须重载一次 df 数据，因为模块导入时路径可能还是空的或旧的
    reload_game_configs()
    
    # 关键修复：重新加载所有业务静态数据 (Sect, Technique等)
    # 确保内存中的对象与当前的语言设置一致。
    # 因为模块导入(import)时可能使用的是默认配置，必须在启动时强制刷新一次。
    reload_all_static_data()
    
    print(f"Current Language: {language_manager}")

    # 启动时不再自动开始初始化游戏，等待前端指令
    # 保持 init_status 为 idle
    print("服务器启动，等待开始游戏指令...")
    
    # 启动后台游戏循环（会自动等待初始化完成）
    asyncio.create_task(game_loop())
    
    npm_process = None
    # 从环境变量或配置文件读取 host。
    host = os.environ.get("SERVER_HOST") or getattr(getattr(CONFIG, "system", None), "host", None) or "127.0.0.1"
    
    if IS_DEV_MODE:
        print("🚀 启动开发模式 (Dev Mode)...")
        # 计算 web 目录 (假设在当前脚本的 ../../web)
        # 注意：这里直接重新计算路径，确保稳健
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        web_dir = os.path.join(project_root, 'web')
        
        print(f"正在启动前端开发服务 (npm run dev) 于: {web_dir}")
        # 跨平台兼容：Windows 用 shell=True + 字符串，macOS/Linux 用 shell=False + 列表。
        try:
            import platform
            if platform.system() == "Windows":
                npm_process = subprocess.Popen("npm run dev", cwd=web_dir, shell=True)
            else:
                npm_process = subprocess.Popen(["npm", "run", "dev"], cwd=web_dir, shell=False)
            # 假设 Vite 默认端口是 5173
            target_url = "http://localhost:5173"
        except Exception as e:
            print(f"启动前端服务失败: {e}")
            target_url = f"http://{host}:8002"
    else:
        target_url = f"http://{host}:8002"
    
    # 自动打开浏览器 (已替换为 pywebview 独立窗口，此处不再打开系统浏览器)
    # print(f"Ready! Opening browser at {target_url}")
    # try:
    #     webbrowser.open(target_url)
    # except Exception as e:
    #     print(f"Failed to open browser: {e}")
        
    yield
    
    # 关闭时清理
    if npm_process:
        print("正在关闭前端开发服务...")
        try:
            import platform
            if platform.system() == "Windows":
                # Windows 下 terminate 可能无法杀死 shell=True 的子进程树。
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(npm_process.pid)])
            else:
                # macOS/Linux 直接 terminate。
                npm_process.terminate()
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
    
    # ===== 检查 LLM 状态并通知前端 =====
    if game_instance.get("llm_check_failed", False):
        error_msg = game_instance.get("llm_error_message", "LLM 连接失败")
        await websocket.send_json({
            "type": "llm_config_required",
            "error": error_msg
        })
        print(f"已向客户端发送 LLM 配置要求: {error_msg}")
    # ===== 检测结束 =====
    
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
                    "action_emoji": resolve_avatar_action_emoji(a),
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


@app.get("/api/events")
def get_events(
    avatar_id: str = None,
    avatar_id_1: str = None,
    avatar_id_2: str = None,
    cursor: str = None,
    limit: int = 100,
):
    """
    分页获取事件列表。

    Query Parameters:
        avatar_id: 按单个角色筛选。
        avatar_id_1: Pair 查询：角色 1。
        avatar_id_2: Pair 查询：角色 2（需同时提供 avatar_id_1）。
        cursor: 分页 cursor，获取该位置之前的事件。
        limit: 每页数量，默认 100。
    """
    world = game_instance.get("world")
    if world is None:
        return {"events": [], "next_cursor": None, "has_more": False}

    event_manager = getattr(world, "event_manager", None)
    if event_manager is None:
        return {"events": [], "next_cursor": None, "has_more": False}

    # 构建 pair 参数
    avatar_id_pair = None
    if avatar_id_1 and avatar_id_2:
        avatar_id_pair = (avatar_id_1, avatar_id_2)

    # 调用分页查询
    events, next_cursor, has_more = event_manager.get_events_paginated(
        avatar_id=avatar_id,
        avatar_id_pair=avatar_id_pair,
        cursor=cursor,
        limit=limit,
    )

    return {
        "events": serialize_events_for_client(events),
        "next_cursor": next_cursor,
        "has_more": has_more,
    }


@app.delete("/api/events/cleanup")
def cleanup_events(
    keep_major: bool = True,
    before_month_stamp: int = None,
):
    """
    清理历史事件（用户触发）。

    Query Parameters:
        keep_major: 是否保留大事，默认 true。
        before_month_stamp: 删除此时间之前的事件。
    """
    world = game_instance.get("world")
    if world is None:
        return {"deleted": 0, "error": "No world"}

    event_manager = getattr(world, "event_manager", None)
    if event_manager is None:
        return {"deleted": 0, "error": "No event manager"}

    deleted = event_manager.cleanup(
        keep_major=keep_major,
        before_month_stamp=before_month_stamp,
    )
    return {"deleted": deleted}


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
            # 如果是宗门区域，传递 sect_id 用于前端加载图片资源
            if hasattr(r, 'sect_id'):
                region_dict["sect_id"] = r.sect_id
            
            # 如果是修炼区域（洞府/遗迹），传递 sub_type
            if hasattr(r, 'sub_type'):
                region_dict["sub_type"] = r.sub_type
            
            regions_data.append(region_dict)
        
    return {
        "width": w,
        "height": h,
        "data": map_data,
        "regions": regions_data,
        "config": CONFIG.get("frontend", {})
    }


@app.get("/api/rankings")
def get_rankings():
    """获取天、地、人及宗门榜单数据"""
    world = game_instance.get("world")
    if not world or not hasattr(world, 'ranking_manager'):
        return {"heaven": [], "earth": [], "human": [], "sect": []}
    
    # 如果榜单为空（比如刚初始化或读档，还没经过1月），主动更新一次
    rm = world.ranking_manager
    if not rm.heaven_ranking and not rm.earth_ranking and not rm.human_ranking and not rm.sect_ranking:
        rm.update_rankings(world.avatar_manager.get_living_avatars())
        
    return rm.get_rankings_data()


@app.post("/api/control/reset")
def reset_game():
    """重置游戏到 Idle 状态（回到主菜单）"""
    game_instance["world"] = None
    game_instance["sim"] = None
    game_instance["is_paused"] = True
    game_instance["init_status"] = "idle"
    game_instance["init_phase"] = 0
    game_instance["init_progress"] = 0
    game_instance["init_error"] = None
    return {"status": "ok", "message": "Game reset to idle"}

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

@app.post("/api/control/shutdown")
async def shutdown_server():
    def _shutdown():
        time.sleep(1) # 给前端一点时间接收 200 OK 响应
        # 这种方式适用于 uvicorn 运行环境，或者直接杀进程
        if IS_DEV_MODE:
            try:
                os.kill(os.getpid(), signal.SIGINT)
                time.sleep(1)
            except Exception:
                pass
        os._exit(0)
    
    # 异步执行关闭，确保先返回响应
    threading.Thread(target=_shutdown).start()
    return {"status": "shutting_down", "message": "Server is shutting down..."}


# --- 初始化状态 API ---

@app.get("/api/init-status")
def get_init_status():
    """获取初始化状态。"""
    status = game_instance.get("init_status", "idle")
    start_time = game_instance.get("init_start_time")
    elapsed = time.time() - start_time if start_time else 0
    
    return {
        "status": status,
        "phase": game_instance.get("init_phase", 0),
        "phase_name": game_instance.get("init_phase_name", ""),
        "progress": game_instance.get("init_progress", 0),
        "elapsed_seconds": round(elapsed, 1),
        "error": game_instance.get("init_error"),
        "version": getattr(getattr(CONFIG, "meta", None), "version", ""),
        # 额外信息：LLM 状态
        "llm_check_failed": game_instance.get("llm_check_failed", False),
        "llm_error_message": game_instance.get("llm_error_message", ""),
    }


# --- 开局配置与启动 API ---

class GameStartRequest(BaseModel):
    init_npc_num: int
    sect_num: int
    npc_awakening_rate_per_month: float
    world_history: Optional[str] = None

@app.get("/api/config/current")
def get_current_config():
    """获取当前游戏配置（用于回显）"""
    return {
        "game": {
            "init_npc_num": getattr(CONFIG.game, "init_npc_num", 12),
            "sect_num": getattr(CONFIG.game, "sect_num", 3),
            "npc_awakening_rate_per_month": getattr(CONFIG.game, "npc_awakening_rate_per_month", 0.01),
            "world_history": getattr(CONFIG.game, "world_history", "")
        },
        "avatar": {}
    }

@app.get("/api/config/llm/status")
def get_llm_status():
    """获取 LLM 配置状态"""
    key = getattr(CONFIG.llm, "key", "")
    base_url = getattr(CONFIG.llm, "base_url", "")
    return {
        "configured": bool(key and base_url)
    }

@app.post("/api/game/start")
async def start_game(req: GameStartRequest):
    """
    保存配置并开始新游戏。
    """
    current_status = game_instance.get("init_status", "idle")
    if current_status == "in_progress":
        raise HTTPException(status_code=400, detail="Game is already initializing")

    # 1. 保存到 local_config.yml
    local_config_path = "static/local_config.yml"
    
    # 读取现有 local_config 或创建新的
    if os.path.exists(local_config_path):
        conf = OmegaConf.load(local_config_path)
    else:
        conf = OmegaConf.create({})
    
    # 确保结构存在
    if "game" not in conf: conf.game = {}
    if "avatar" not in conf: conf.avatar = {}
    
    # 更新值
    conf.game.init_npc_num = req.init_npc_num
    conf.game.sect_num = req.sect_num
    conf.game.npc_awakening_rate_per_month = req.npc_awakening_rate_per_month
    conf.game.world_history = req.world_history or ""
    
    # 写入文件
    try:
        OmegaConf.save(conf, local_config_path)
    except Exception as e:
        print(f"Error saving local config: {e}")
        # Log but continue? Or fail? Best to fail if we promised to save.
        raise HTTPException(status_code=500, detail=f"Failed to save config: {e}")

    # 2. 重新加载全局 CONFIG
    global CONFIG
    try:
        # 重新执行 load_config
        new_config = load_config()
        # 更新 CONFIG 引用 (OmegaConf 对象是可变的吗？ load_config 返回新对象)
        # 我们不能简单替换 import 的 CONFIG，因为其他模块可能已经 import 了它。
        # OmegaConf.merge 是原地更新吗？ 不是。
        # 这是一个常见坑。最好的方式是修改 CONFIG 的内容而不是替换对象。
        # 但 CONFIG 是 DictConfig。
        
        # 让我们尝试更新 CONFIG 的内容
        # 更好的方法可能是：
        CONFIG.merge_with(new_config) 
        
    except Exception as e:
        print(f"Error reloading config: {e}")
    
    # 3. 开始初始化
    if current_status == "ready":
        # 清理旧的游戏状态
        game_instance["world"] = None
        game_instance["sim"] = None
    
    game_instance["init_status"] = "pending"
    game_instance["init_phase"] = 0
    game_instance["init_progress"] = 0
    game_instance["init_error"] = None
    
    # 启动异步初始化任务
    asyncio.create_task(init_game_async())
    
    return {"status": "ok", "message": "Game initialization started"}


@app.post("/api/control/reinit")
async def reinit_game():
    """重新初始化游戏（用于错误恢复）。"""
    # 清理旧的游戏状态
    game_instance["world"] = None
    game_instance["sim"] = None
    game_instance["init_status"] = "pending"
    game_instance["init_phase"] = 0
    game_instance["init_progress"] = 0
    game_instance["init_error"] = None
    
    # 启动异步初始化任务
    asyncio.create_task(init_game_async())
    
    return {"status": "ok", "message": "Reinitialization started"}


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
        target = world.avatar_manager.get_avatar(target_id)
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
         
    info = target.get_structured_info()
    return info

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
            "sect_id": t.sect_id
        }
        for t in techniques_by_id.values()
    ]

    weapons_list = [
        {
            "id": w.id,
            "name": w.name,
            "type": w.weapon_type.value,
            "grade": w.realm.value,
        }
        for w in weapons_by_id.values()
    ]

    auxiliaries_list = [
        {
            "id": a.id,
            "name": a.name,
            "grade": a.realm.value,
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
            "gender": str(a.gender),
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
                if language_manager.current == LanguageType.EN_US:
                    final_name = f"{surname} {given_name}"
                else:
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
        world.avatar_manager.register_avatar(avatar, is_newly_born=True)
        
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


# --- LLM Config API ---

class LanguageRequest(BaseModel):
    lang: str

@app.get("/api/config/language")
def get_language_api():
    """获取当前语言设置"""
    return {"lang": str(language_manager)}

@app.post("/api/config/language")
def set_language_api(req: LanguageRequest):
    """设置并保存语言设置"""
    # 1. 更新内存
    language_manager.set_language(req.lang)
    
    # 2. 更新路径配置
    from src.utils.config import update_paths_for_language
    update_paths_for_language(req.lang)
    
    # 3. 重新加载 CSV 数据
    from src.utils.df import reload_game_configs
    reload_game_configs()
    
    # 4. 重新加载所有业务静态数据 (Sects, Techniques, etc.)
    reload_all_static_data()
    
    # 修复运行时引用 (热重载后，运行时对象指向的静态对象引用过时)
    world = game_instance.get("world")
    if world:
        from src.run.data_loader import fix_runtime_references
        fix_runtime_references(world)
    
    # 5. 持久化到 local_config.yml
    local_config_path = "static/local_config.yml"
    try:
        if os.path.exists(local_config_path):
            conf = OmegaConf.load(local_config_path)
        else:
            conf = OmegaConf.create({})
        
        if "system" not in conf:
            conf.system = {}
            
        conf.system.language = str(language_manager)
        
        OmegaConf.save(conf, local_config_path)
        
        # 同时更新全局 CONFIG (虽然下次重启才会完全生效，但保持一致性)
        if not hasattr(CONFIG, "system"):
            # 这是一个 hack，因为 DictConfig 可能不支持动态添加属性，除非是 struct mode=false
            # OmegaConf 默认加载出来的通常是开放的
            pass 
        
        return {"status": "ok"}
    except Exception as e:
        print(f"Error saving language config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save language config: {e}")

class LLMConfigDTO(BaseModel):
    base_url: str
    api_key: Optional[str] = ""
    model_name: str
    fast_model_name: str
    mode: str
    max_concurrent_requests: Optional[int] = 10

class TestConnectionRequest(BaseModel):
    base_url: str
    api_key: Optional[str] = ""
    model_name: str

@app.get("/api/config/llm")
def get_llm_config():
    """获取当前 LLM 配置"""
    return {
        "base_url": getattr(CONFIG.llm, "base_url", ""),
        "api_key": getattr(CONFIG.llm, "key", ""),
        "model_name": getattr(CONFIG.llm, "model_name", ""),
        "fast_model_name": getattr(CONFIG.llm, "fast_model_name", ""),
        "mode": getattr(CONFIG.llm, "mode", "default"),
        "max_concurrent_requests": getattr(CONFIG.ai, "max_concurrent_requests", 10)
    }

@app.post("/api/config/llm/test")
def test_llm_connection(req: TestConnectionRequest):
    """测试 LLM 连接"""
    try:
        # 构造临时配置
        config = LLMConfig(
            base_url=req.base_url,
            api_key=req.api_key,
            model_name=req.model_name
        )
        
        success, error_msg = test_connectivity(config=config)
        
        if success:
            return {"status": "ok", "message": "连接成功"}
        else:
            # 返回 400 错误并附带详细的错误信息
            raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        # 重新抛出 HTTPException
        raise
    except Exception as e:
        # 其他未预期的错误
        raise HTTPException(status_code=500, detail=f"测试出错: {str(e)}")

@app.post("/api/config/llm/save")
async def save_llm_config(req: LLMConfigDTO):
    """保存 LLM 配置"""
    try:
        # 1. Update In-Memory Config (Partial update)
        # OmegaConf object attributes can be set directly if they exist
        if not OmegaConf.is_config(CONFIG):
            # 理论上 CONFIG 是 DictConfig
            pass

        # 直接更新 CONFIG.llm 的属性
        CONFIG.llm.base_url = req.base_url
        CONFIG.llm.key = req.api_key
        CONFIG.llm.model_name = req.model_name
        CONFIG.llm.fast_model_name = req.fast_model_name
        CONFIG.llm.mode = req.mode

        # 更新 ai 配置
        if req.max_concurrent_requests:
            if not hasattr(CONFIG, "ai"):
                 CONFIG.ai = OmegaConf.create({})
            CONFIG.ai.max_concurrent_requests = req.max_concurrent_requests

        # 2. Persist to local_config.yml
        # 使用 src/utils/config.py 中类似的路径逻辑
        # 注意：这里我们假设是在项目根目录下运行，或者静态文件路径是相对固定的
        # 为了稳健，我们复用 CONFIG 加载时的路径逻辑（但这里是写入）
        
        local_config_path = "static/local_config.yml"
        
        # Load existing or create new
        if os.path.exists(local_config_path):
            conf = OmegaConf.load(local_config_path)
        else:
            conf = OmegaConf.create({})
        
        # Ensure llm section exists
        if "llm" not in conf:
            conf.llm = {}
            
        conf.llm.base_url = req.base_url
        conf.llm.key = req.api_key
        conf.llm.model_name = req.model_name
        conf.llm.fast_model_name = req.fast_model_name
        conf.llm.mode = req.mode

        # Ensure ai section exists and update
        if req.max_concurrent_requests:
            if "ai" not in conf:
                conf.ai = {}
            conf.ai.max_concurrent_requests = req.max_concurrent_requests
        
        OmegaConf.save(conf, local_config_path)
        
        # ===== 如果之前 LLM 连接失败，现在恢复运行 =====
        if game_instance.get("llm_check_failed", False):
            print("检测到之前 LLM 连接失败，正在恢复 Simulator 运行...")
            
            # 清除失败标志并恢复运行
            game_instance["llm_check_failed"] = False
            game_instance["llm_error_message"] = ""
            game_instance["is_paused"] = False
            
            print("Simulator 已恢复运行")
            
            # 通知所有客户端刷新
            await manager.broadcast({
                "type": "game_reinitialized",
                "message": "LLM 配置成功，游戏已恢复运行"
            })
        # ===== 恢复运行结束 =====
        
        return {"status": "ok", "message": "配置已保存"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


# --- 存档系统 API ---

def validate_save_name(name: str) -> bool:
    """验证存档名称是否合法。"""
    if not name or len(name) > 50:
        return False
    # 只允许中文、字母、数字和下划线。
    pattern = r'^[\w\u4e00-\u9fff]+$'
    return bool(re.match(pattern, name))


class SaveGameRequest(BaseModel):
    custom_name: Optional[str] = None  # 自定义存档名称

class DeleteSaveRequest(BaseModel):
    filename: str

class LoadGameRequest(BaseModel):
    filename: str

@app.get("/api/saves")
def get_saves():
    """获取存档列表"""
    saves_list = list_saves()
    # 转换 Path 为 str，并整理格式。
    result = []
    for path, meta in saves_list:
        result.append({
            "filename": path.name,
            "save_time": meta.get("save_time", ""),
            "game_time": meta.get("game_time", ""),
            "version": meta.get("version", ""),
            # 新增字段。
            "language": meta.get("language", ""),
            "avatar_count": meta.get("avatar_count", 0),
            "alive_count": meta.get("alive_count", 0),
            "dead_count": meta.get("dead_count", 0),
            "custom_name": meta.get("custom_name"),
            "event_count": meta.get("event_count", 0),
        })
    return {"saves": result}

@app.post("/api/game/save")
def api_save_game(req: SaveGameRequest):
    """保存游戏"""
    world = game_instance.get("world")
    sim = game_instance.get("sim")
    if not world or not sim:
        raise HTTPException(status_code=503, detail="Game not initialized")

    # 尝试从 world 属性获取（如果以后添加了）。
    existed_sects = getattr(world, "existed_sects", [])
    if not existed_sects:
        # fallback: 所有 sects.
        existed_sects = list(sects_by_id.values())

    # 名称验证。
    custom_name = req.custom_name
    if custom_name and not validate_save_name(custom_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid save name"
        )

    # 新存档（不使用 current_save_path，每次创建新文件）。
    success, filename = save_game(world, sim, existed_sects, custom_name=custom_name)
    if success:
        return {"status": "ok", "filename": filename}
    else:
        raise HTTPException(status_code=500, detail="Save failed")

@app.post("/api/game/delete")
def api_delete_game(req: DeleteSaveRequest):
    """删除存档及其关联文件"""
    # 安全检查
    if ".." in req.filename or "/" in req.filename or "\\" in req.filename:
         raise HTTPException(status_code=400, detail="Invalid filename")

    try:
        saves_dir = CONFIG.paths.saves
        target_path = saves_dir / req.filename
        
        # 1. 删除 JSON 存档文件
        if target_path.exists():
            os.remove(target_path)
            
        # 2. 删除对应的 SQL 数据库文件
        events_db_path = get_events_db_path(target_path)
        if os.path.exists(events_db_path):
            try:
                os.remove(events_db_path)
            except Exception as e:
                print(f"[Warning] Failed to delete db file {events_db_path}: {e}")
                
        # 3. 删除可能存在的其他关联文件（如果有）
        
        return {"status": "ok", "message": "Save deleted"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.post("/api/game/load")
async def api_load_game(req: LoadGameRequest):
    """加载游戏（异步，支持进度更新）。"""
    # 安全检查：只允许加载 saves 目录下的文件
    if ".." in req.filename or "/" in req.filename or "\\" in req.filename:
         raise HTTPException(status_code=400, detail="Invalid filename")
    
    try:
        saves_dir = CONFIG.paths.saves
        target_path = saves_dir / req.filename
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # --- 语言环境自动切换 ---
        from src.sim import get_save_info
        save_meta = get_save_info(target_path)
        if save_meta:
            save_lang = save_meta.get("language")
            current_lang = str(language_manager)
            
            print(f"[Debug] Load Game - Save Lang: {save_lang}, Current Lang: {current_lang}")

            # 无论后端是否已经是该语言，都强制通知前端切换
            # 这样可以解决 "前端手动刷新回中文，但后端还是英文，导致不再发送切换指令" 的问题
            if save_lang:
                print(f"[Auto-Switch] Enforcing language sync to {save_lang}...")
                
                # 1. 通知前端
                await manager.broadcast({
                    "type": "toast",
                    "level": "info",
                    "message": f"正在同步语言设置: {save_lang}...",
                    "language": save_lang
                })

                # Yield control to event loop
                await asyncio.sleep(0.2)
                
                # 2. 只有当后端语言确实不同步时，才执行后端切换逻辑
                if save_lang != current_lang:
                    print(f"[Auto-Switch] Switching backend language from {current_lang} to {save_lang}...")
                    # 切换语言 (放到线程池执行)
                    await asyncio.to_thread(language_manager.set_language, save_lang)
                    
                    # 重新加载所有静态业务数据
                    await asyncio.to_thread(reload_all_static_data)
                    
                    # 持久化语言设置
                    local_config_path = "static/local_config.yml"
                    try:
                        if os.path.exists(local_config_path):
                            conf = OmegaConf.load(local_config_path)
                        else:
                            conf = OmegaConf.create({})
                        
                        if "system" not in conf:
                            conf.system = OmegaConf.create({})
                        conf.system.language = save_lang
                        OmegaConf.save(conf, local_config_path)
                    except Exception as e:
                        print(f"Warning: Failed to persist language switch: {e}")
        # -----------------------

        # 设置加载状态
        game_instance["init_status"] = "in_progress"
        game_instance["init_start_time"] = time.time()
        game_instance["init_error"] = None
        game_instance["init_phase"] = 0
        
        # 0. 扫描资源 (修复读取存档不加载头像的问题)
        game_instance["init_phase_name"] = "scanning_assets"
        await asyncio.to_thread(scan_avatar_assets)

        game_instance["init_phase_name"] = "loading_save"
        game_instance["init_progress"] = 10

        # 暂停游戏，防止 game_loop 在加载过程中使用旧 world 生成事件。
        game_instance["is_paused"] = True
        await asyncio.sleep(0)  # 让出控制权

        # 更新进度
        game_instance["init_progress"] = 30
        game_instance["init_phase_name"] = "parsing_data"
        await asyncio.sleep(0)

        # 关闭旧 World 的 EventManager，释放 SQLite 连接。
        old_world = game_instance.get("world")
        if old_world and hasattr(old_world, "event_manager"):
            old_world.event_manager.close()

        # 加载
        new_world, new_sim, new_sects = load_game(target_path)
        
        # 更新进度
        game_instance["init_progress"] = 70
        game_instance["init_phase_name"] = "restoring_state"
        await asyncio.sleep(0)

        # 确保挂载 existed_sects 以便下次保存
        new_world.existed_sects = new_sects

        # 替换全局实例
        game_instance["world"] = new_world
        game_instance["sim"] = new_sim
        game_instance["current_save_path"] = target_path

        # 更新进度
        game_instance["init_progress"] = 90
        game_instance["init_phase_name"] = "finalizing"
        await asyncio.sleep(0)

        # 加载完成
        game_instance["init_status"] = "ready"
        game_instance["init_progress"] = 100
        game_instance["init_phase_name"] = "complete"
        
        # 加载完成后保持暂停状态，让用户决定何时恢复。
        # 这也给前端时间来刷新状态。
        
        return {"status": "ok", "message": "Game loaded"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        game_instance["init_status"] = "error"
        game_instance["init_error"] = str(e)
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
    # 从环境变量或配置文件读取服务器配置。
    host = os.environ.get("SERVER_HOST") or getattr(getattr(CONFIG, "system", None), "host", None) or "127.0.0.1"
    port = int(os.environ.get("SERVER_PORT") or getattr(getattr(CONFIG, "system", None), "port", None) or 8002)

    # 计算目标 URL (与 lifespan 中的逻辑保持一致)
    target_url = f"http://{host}:{port}"
    if IS_DEV_MODE:
        # 开发模式下，前端通常运行在 5173
        target_url = "http://localhost:5173"

    def run_server():
        """在子线程中运行 uvicorn 服务器"""
        # log_level="error" 可以减少控制台噪音，根据需要调整
        uvicorn.run(app, host=host, port=port, log_level="info")

    # 1. 启动后端服务器线程 (daemon=True 确保主线程退出时子线程也退出)
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # 2. 创建独立窗口
    # width/height 可根据游戏设计调整，min_size 确保布局不崩坏
    webview.create_window(
        title="Cultivation Simulator", 
        url=target_url,
        width=1280,
        height=800,
        min_size=(1024, 768),
        confirm_close=True  # 关闭时确认
    )

    # 3. 启动 GUI (必须在主线程运行)
    print(f"Starting GUI window loading {target_url}...")
    webview.start(debug=False)

    # 4. 窗口关闭后，通过杀进程方式确保 uvicorn 和 subprocess彻底关闭
    print("Window closed, shutting down...")
    if IS_DEV_MODE:
        try:
            os.kill(os.getpid(), signal.SIGINT)
            time.sleep(1)
        except Exception:
            pass
    os._exit(0)

if __name__ == "__main__":
    start()