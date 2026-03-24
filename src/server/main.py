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
import subprocess
import time
import threading
import signal
import random
import hashlib
import re
import logging
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
from src.server.assemblers.sect_detail import build_sect_detail
from src.server.assemblers.mortal_overview import build_mortal_overview
from src.server.assemblers.dynasty_detail import build_dynasty_detail
from src.server.assemblers.dynasty_overview import build_dynasty_overview
from src.run.load_map import load_cultivation_world_map
from src.sim.avatar_init import make_avatars as _new_make_random, create_avatar_from_request
from src.systems.dynasty_generator import generate_dynasty, generate_emperor
from src.utils.config import CONFIG
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
from src.classes.language import language_manager
from src.systems.sect_relations import compute_sect_relations
from src.i18n import t
from src.config import AppSettingsPatch, LLMSettingsUpdate, RunConfig, get_settings_service
from src.i18n.locale_registry import uses_space_separated_names

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
    "run_config": None,      # 当前运行中的开局参数快照
}

# Cache for avatar IDs
AVATAR_ASSETS = {
    "males": [],
    "females": []
}


def _model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def get_runtime_run_config() -> RunConfig:
    run_config = game_instance.get("run_config")
    if run_config:
        return RunConfig(**run_config)

    defaults = get_settings_service().get_default_run_config()
    game_conf = getattr(CONFIG, "game", None)
    return RunConfig(
        content_locale=defaults.content_locale,
        init_npc_num=int(getattr(game_conf, "init_npc_num", defaults.init_npc_num)),
        sect_num=int(getattr(game_conf, "sect_num", defaults.sect_num)),
        npc_awakening_rate_per_month=float(
            getattr(game_conf, "npc_awakening_rate_per_month", defaults.npc_awakening_rate_per_month)
        ),
        world_history=str(getattr(game_conf, "world_history", defaults.world_history) or ""),
    )


def apply_runtime_content_locale(lang_code: str) -> None:
    from src.utils.config import update_paths_for_language
    from src.utils.df import reload_game_configs

    language_manager.set_language(lang_code)
    update_paths_for_language(lang_code)
    reload_game_configs()
    reload_all_static_data()

    world = game_instance.get("world")
    if world:
        from src.run.data_loader import fix_runtime_references
        fix_runtime_references(world)

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
        
    # 使用 hashlib.md5 生成跨进程稳定的整数 hash
    hash_bytes = hashlib.md5(str(avatar_id).encode('utf-8')).digest()
    # 取前4个字节转换为整数即可满足均匀分布的需求
    hash_int = int.from_bytes(hash_bytes[:4], byteorder='little')
    idx = hash_int % len(available)
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
        self._shutdown_timer: threading.Timer = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # 取消可能存在的关机定时器
        if self._shutdown_timer:
            self._shutdown_timer.cancel()
            self._shutdown_timer = None
        
        # 不再自动恢复游戏，让用户明确选择"新游戏"或"加载存档"。
        # 这样可以避免在用户加载存档前就生成初始化事件。
        if len(self.active_connections) == 1:
            print("[Auto-Control] Client connection detected, game paused, waiting for user input.")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        # 当最后一个客户端断开时，自动暂停游戏
        if len(self.active_connections) == 0:
            self._set_pause_state(True, "所有客户端已断开，自动暂停游戏以节省资源。")
            
            # 在非开发模式下，如果所有客户端断开，自动关闭服务器
            if not IS_DEV_MODE:
                print("[Auto-Control] All clients disconnected. Server will shutdown in 5 seconds...")
                def _do_shutdown():
                    print("[Auto-Control] Auto shutdown triggered due to no active connections.")
                    os._exit(0)
                self._shutdown_timer = threading.Timer(5.0, _do_shutdown)
                self._shutdown_timer.start()

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

        related_sects_raw = getattr(event, "related_sects", None) or []
        related_sect_ids = [int(s) for s in related_sects_raw if s is not None]

        serialized.append({
            "id": getattr(event, "id", None) or f"{stamp_int or 'evt'}-{idx}",
            "text": str(event),
            "content": getattr(event, "content", ""),
            "year": year,
            "month": month,
            "month_stamp": stamp_int,
            "related_avatar_ids": related_ids,
            "related_sects": related_sect_ids,
            "is_major": bool(getattr(event, "is_major", False)),
            "is_story": bool(getattr(event, "is_story", False)),
            "render_key": getattr(event, "render_key", None),
            "render_params": getattr(event, "render_params", None),
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
            print(f"Testing LLM connectivity (Single Model): {normal_config.model_name}")
            success, error = test_connectivity(LLMMode.NORMAL, normal_config)
            if not success:
                return False, f"连接失败：{error}"
        else:
            # 测试两次
            print(f"Testing normal model connectivity: {normal_config.model_name}")
            success, error = test_connectivity(LLMMode.NORMAL, normal_config)
            if not success:
                return False, f"智能模型连接失败：{error}"
            
            print(f"Testing fast model connectivity: {fast_config.model_name}")
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
        print("Resetting world rule data...")
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
        print(f"Events database: {events_db_path}")

        run_config = get_runtime_run_config()
        start_year = getattr(CONFIG.game, "start_year", 100)
        world = World.create_with_db(
            map=game_map,
            month_stamp=create_month_stamp(Year(start_year), Month.JANUARY),
            events_db_path=events_db_path,
            start_year=start_year,
        )
        world.dynasty = generate_dynasty()
        world.dynasty.current_emperor = generate_emperor(world.dynasty, int(world.month_stamp))
        world.event_manager.add_event(
            Event(
                month_stamp=world.month_stamp,
                content=t(
                    "{dynasty_title} has enthroned a new ruler, and {emperor_name} ascends as emperor.",
                    dynasty_title=world.dynasty.title,
                    emperor_name=world.dynasty.current_emperor.name,
                ),
                is_major=True,
            )
        )
        sim = Simulator(world)
        sim.awakening_rate = run_config.npc_awakening_rate_per_month
        world.run_config_snapshot = _model_to_dict(run_config)

        # 阶段 2: 历史背景影响 (如果配置了历史)
        update_init_progress(2, "processing_history")
        world_history = run_config.world_history
        if world_history and world_history.strip():
            world.set_history(world_history)
            print(f"Reshaping world based on historical background: {world_history[:50]}...")
            try:
                history_mgr = HistoryManager(world)
                await history_mgr.apply_history_influence(world_history)
                print("Historical background applied")
            except Exception as e:
                print(f"[Warning] Failed to apply historical background: {e}")
        
        # 阶段 3: 宗门初始化
        update_init_progress(3, "initializing_sects")
        all_sects = list(sects_by_id.values())
        needed_sects = int(run_config.sect_num or 0)
        existed_sects = []
        if needed_sects > 0 and all_sects:
            pool = list(all_sects)
            random.shuffle(pool)
            existed_sects = pool[:needed_sects]

        # 阶段 4: 角色生成
        update_init_progress(4, "generating_avatars")
        target_total_count = int(run_config.init_npc_num)
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
            print(f"Generated {len(random_avatars)} random NPCs")

        world.avatar_manager.avatars.update(final_avatars)
        world.existed_sects = existed_sects
        # 使用 SectContext 统一记录本局启用宗门作用域
        world.sect_context.from_existed_sects(existed_sects)
        game_instance["world"] = world
        game_instance["sim"] = sim

        # 阶段 5: LLM 连通性检测
        update_init_progress(5, "checking_llm")
        print("Checking LLM connectivity...")
        # 使用线程池执行，避免阻塞事件循环，让 /api/init-status 可以响应
        success, error_msg = await asyncio.to_thread(check_llm_connectivity)

        if not success:
            print(f"[Warning] LLM connectivity check failed: {error_msg}")
            game_instance["llm_check_failed"] = True
            game_instance["llm_error_message"] = error_msg
        else:
            print("LLM connectivity check passed")
            game_instance["llm_check_failed"] = False
            game_instance["llm_error_message"] = ""

        # 阶段 6: 生成初始事件（第一次 sim.step）
        update_init_progress(6, "generating_initial_events")
        print("Generating initial events...")
        
        # 取消暂停，执行第一步来生成初始事件
        game_instance["is_paused"] = False
        try:
            await sim.step()
            print("Initial events generation completed")
        except Exception as e:
            print(f"[Warning] Initial events generation failed: {e}")
        finally:
            # 执行完后重新暂停，等待前端准备好
            game_instance["is_paused"] = True

        # 完成
        game_instance["init_status"] = "ready"
        game_instance["init_progress"] = 100
        print("Game world initialization completed!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        game_instance["init_status"] = "error"
        game_instance["init_error"] = str(e)
        print(f"[Error] Initialization failed: {e}")



def trigger_auto_save(world, sim):
    """提取的自动保存逻辑，供 game_loop 和测试使用"""
    playthrough_id = getattr(world, "playthrough_id", "")
    max_auto_saves = get_settings_service().get_settings().simulation.max_auto_saves
    
    # 1. 获取当前局的所有自动存档
    all_saves = list_saves()
    auto_saves = []
    for path, meta in all_saves:
        if meta.get("is_auto_save", False) and meta.get("playthrough_id", "") == playthrough_id:
            auto_saves.append((path, meta))
            
    # 2. 如果数量 >= 上限，删除最老的
    # list_saves 已经是按时间倒序排列的，所以最老的是在列表末尾
    while len(auto_saves) >= max_auto_saves:
        oldest_path, oldest_meta = auto_saves.pop()
        # 删除旧存档
        if oldest_path.exists():
            try:
                import os
                os.remove(oldest_path)
                # 同时删除对应的 db 文件
                db_path = get_events_db_path(oldest_path)
                if db_path.exists():
                    os.remove(db_path)
                print(f"[Auto-Save] Removed old auto save: {oldest_path.name}")
            except Exception as e:
                print(f"[Auto-Save] Failed to remove old auto save: {e}")
                
    # 3. 创建新存档
    existed_sects = getattr(world, "existed_sects", [])
    if not existed_sects:
        existed_sects = list(sects_by_id.values())
    
    save_game(world, sim, existed_sects, is_auto_save=True)

async def game_loop():
    """后台自动运行游戏循环。"""
    print("Background game loop started, waiting for initialization...")
    
    # 等待初始化完成
    while game_instance.get("init_status") not in ("ready", "error"):
        await asyncio.sleep(0.5)
    
    if game_instance.get("init_status") == "error":
        print("[game_loop] Initialization failed, game loop exiting.")
        return
    
    print("[game_loop] Initialization completed, starting game loop.")
    
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
                
                # ======== 自动保存逻辑 ========
                # 检查是否启用了自动保存
                auto_save_enabled = get_settings_service().get_settings().simulation.auto_save_enabled
                year = int(world.month_stamp.get_year())
                month = world.month_stamp.get_month().value
                
                # 触发条件：每10年的1月，且不是第一年
                if auto_save_enabled and year % 10 == 0 and month == 1 and year > world.start_year:
                    print(f"[Auto-Save] Triggering auto save for year {year}...")
                    # 使用 asyncio.to_thread 防止阻塞主循环
                    await asyncio.to_thread(trigger_auto_save, world, sim)
                    
                    # 通知前端
                    from src.i18n import t
                    await manager.broadcast({
                        "type": "toast",
                        "level": "info",
                        "message": t("Game automatically saved")
                    })
                    print("[Auto-Save] Auto save completed.")
                # ======== 自动保存逻辑结束 ========
                
        except Exception as e:
            from src.run.log import get_logger
            print(f"Game loop error: {e}")
            get_logger().logger.error(f"Game loop error: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Filter out health check / polling logs
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

    settings = get_settings_service().get_settings_view()
    apply_runtime_content_locale(settings.new_game_defaults.content_locale)
    print(f"Current Language: {language_manager}")

    # 启动时不再自动开始初始化游戏，等待前端指令
    # 保持 init_status 为 idle
    print("Server started, waiting for start game command...")
    
    # 启动后台游戏循环（会自动等待初始化完成）
    asyncio.create_task(game_loop())
    
    npm_process = None
    # 从环境变量或配置文件读取 host。
    host = os.environ.get("SERVER_HOST") or getattr(getattr(CONFIG, "system", None), "host", None) or "127.0.0.1"
    
    if IS_DEV_MODE:
        print("🚀 Starting Development Mode (Dev Mode)...")
        # 计算 web 目录 (假设在当前脚本的 ../../web)
        # 注意：这里直接重新计算路径，确保稳健
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        web_dir = os.path.join(project_root, 'web')
        
        print(f"Starting frontend dev server (npm run dev) at: {web_dir}")
        # 跨平台兼容：Windows 用 shell=True + 字符串，macOS/Linux 用 shell=False + 列表。
        try:
            import platform
            vite_port = os.environ.get("VITE_PORT", "5173")
            if platform.system() == "Windows":
                # Vite 有时候会在端口已经被占用的情况下报错并且 strictPort 不起作用
                # 直接通过 npx vite --port XXX 可以避免 npm run dev 的参数传递问题
                cmd = f"npx vite --port {vite_port} --strictPort"
                npm_process = subprocess.Popen(cmd, cwd=web_dir, shell=True)
            else:
                npm_process = subprocess.Popen(["npx", "vite", "--port", vite_port, "--strictPort"], cwd=web_dir, shell=False)
            # 设置最终打开的URL
            target_url = f"http://localhost:{vite_port}"
        except Exception as e:
            print(f"Failed to start frontend server: {e}")
            target_url = f"http://{host}:8002"
    else:
        target_url = f"http://{host}:8002"
    
    # 浏览器打开逻辑统一放在 start() 中处理，避免在 lifespan 阶段重复触发。
        
    yield
    
    # 关闭时清理
    if npm_process:
        print("Closing frontend dev server...")
        try:
            import platform
            if platform.system() == "Windows":
                # Windows 下 terminate 可能无法杀死 shell=True 的子进程树。
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(npm_process.pid)])
            else:
                # macOS/Linux 直接 terminate。
                npm_process.terminate()
        except Exception as e:
            print(f"Error closing frontend server: {e}")

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
        print(f"Sent LLM configuration requirement to client: {error_msg}")
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
    sect_id: int = None,
    cursor: str = None,
    limit: int = 100,
):
    """
    分页获取事件列表。

    Query Parameters:
        avatar_id: 按单个角色筛选。
        avatar_id_1: Pair 查询：角色 1。
        avatar_id_2: Pair 查询：角色 2（需同时提供 avatar_id_1）。
        sect_id: 按宗门筛选。
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
        sect_id=sect_id,
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
                "y": r.center_loc[1],
            }
            # 如果是宗门区域，传递 sect_id、sect_name 以及是否激活状态，用于前端加载图片与筛选展示
            if hasattr(r, "sect_id"):
                region_dict["sect_id"] = r.sect_id
                region_dict["sect_name"] = (
                    getattr(r, "sect_name", None)
                    or (sects_by_id.get(r.sect_id).name if r.sect_id in sects_by_id else None)
                )
                sect_obj = sects_by_id.get(r.sect_id)
                if sect_obj is not None:
                    # 标记该宗门当前是否仍为激活状态（用于事件面板筛选）
                    region_dict["sect_is_active"] = getattr(sect_obj, "is_active", True)
                    # 宗门固定颜色（来自 sect.csv），用于前端事件高亮等场景
                    region_dict["sect_color"] = getattr(sect_obj, "color", "#FFFFFF")
            
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
    if not world or not hasattr(world, "ranking_manager"):
        return {"heaven": [], "earth": [], "human": [], "sect": []}

    # 如果榜单为空（比如刚初始化或读档，还没经过1月），主动更新一次
    rm = world.ranking_manager
    if (
        not rm.heaven_ranking
        and not rm.earth_ranking
        and not rm.human_ranking
        and not rm.sect_ranking
    ):
        rm.update_rankings_with_world(world, world.avatar_manager.get_living_avatars())

    return rm.get_rankings_data()


@app.get("/api/sect-relations")
def get_sect_relations():
    """
    获取宗门之间的关系数据。
    仅包含当前仍然激活的宗门。
    """
    world = game_instance.get("world")
    if world is None:
        return {"relations": []}

    sim = game_instance.get("sim")
    sect_manager = getattr(sim, "sect_manager", None)
    if sect_manager is None:
        from src.sim.managers.sect_manager import SectManager
        sect_manager = SectManager(world)

    from src.sim.managers.sect_manager import SectManager as SectManagerType
    assert isinstance(sect_manager, SectManagerType)

    snapshot = sect_manager.get_snapshot()
    active_sects = snapshot.active_sects
    if not active_sects:
        return {"relations": []}

    extra_breakdown_by_pair = world.get_active_sect_relation_breakdown()
    diplomacy_by_pair = world.get_active_sect_diplomacy_breakdown(
        sect_ids=[int(s.id) for s in active_sects]
    )
    relations = compute_sect_relations(
        active_sects,
        snapshot.tile_owners,
        border_contact_counts=snapshot.border_contact_counts,
        extra_breakdown_by_pair=extra_breakdown_by_pair,
        diplomacy_by_pair=diplomacy_by_pair,
    )
    return {"relations": relations}


@app.get("/api/sects/territories")
def get_sect_territories():
    """
    获取当前活跃宗门的势力范围摘要，供地图常驻渲染使用。
    """
    world = game_instance.get("world")
    if world is None:
        return {"sects": []}

    sim = game_instance.get("sim")
    sect_manager = getattr(sim, "sect_manager", None)
    if sect_manager is None:
        from src.sim.managers.sect_manager import SectManager
        sect_manager = SectManager(world)

    from src.sim.managers.sect_manager import SectManager as SectManagerType
    assert isinstance(sect_manager, SectManagerType)

    snapshot = sect_manager.get_snapshot()
    sects = [
        {
            "id": int(sect.id),
            "name": sect.name,
            "color": str(getattr(sect, "color", "#FFFFFF") or "#FFFFFF"),
            "influence_radius": int(getattr(sect, "influence_radius", 0)),
            "is_active": bool(getattr(sect, "is_active", True)),
            "owned_tiles": [
                {"x": int(x), "y": int(y)}
                for x, y in snapshot.owned_tiles_by_sect.get(int(sect.id), [])
            ],
            "boundary_edges": list(snapshot.boundary_edges_by_sect.get(int(sect.id), [])),
        }
        for sect in snapshot.active_sects
    ]
    return {"sects": sects}


@app.get("/api/mortals/overview")
def get_mortal_overview():
    """获取凡人系统总览数据。"""
    world = game_instance.get("world")
    if world is None:
        return {
            "summary": {
                "total_population": 0.0,
                "total_population_capacity": 0.0,
                "total_natural_growth": 0.0,
                "tracked_mortal_count": 0,
                "awakening_candidate_count": 0,
            },
            "cities": [],
            "tracked_mortals": [],
        }

    return build_mortal_overview(world)


@app.get("/api/dynasty/overview")
def get_dynasty_overview():
    """获取当前王朝总览数据。"""
    world = game_instance.get("world")
    if world is None:
        return build_dynasty_overview(None)

    return build_dynasty_overview(world)


@app.get("/api/dynasty/detail")
def get_dynasty_detail():
    """获取当前王朝详情数据。"""
    world = game_instance.get("world")
    return build_dynasty_detail(world)


@app.post("/api/control/reset")
def reset_game():
    """重置游戏到 Idle 状态（回到主菜单）"""
    game_instance["world"] = None
    game_instance["sim"] = None
    game_instance["current_save_path"] = None
    game_instance["run_config"] = None
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

class GameStartRequest(RunConfig):
    pass

@app.get("/api/settings")
def get_settings():
    """获取统一的应用设置。"""
    return _model_to_dict(get_settings_service().get_settings_view())


@app.patch("/api/settings")
def patch_settings(req: AppSettingsPatch):
    """更新应用设置（不包含敏感信息）。"""
    updated = get_settings_service().patch_settings(req)
    return _model_to_dict(updated)


@app.post("/api/settings/reset")
def reset_settings():
    """重置应用设置和 secrets。"""
    updated = get_settings_service().reset_settings()
    return _model_to_dict(updated)


@app.get("/api/settings/llm")
def get_llm_settings():
    """获取当前 LLM 设置（不返回 API Key）。"""
    return _model_to_dict(get_settings_service().get_llm_view())


@app.get("/api/settings/llm/status")
def get_llm_status():
    """获取 LLM 设置是否可用。"""
    profile, api_key = get_settings_service().get_llm_runtime_config()
    configured = bool(profile.base_url and profile.model_name and api_key)
    return {"configured": configured}

@app.post("/api/game/start")
async def start_game(req: GameStartRequest):
    """
    保存本局运行参数并开始新游戏。
    """
    current_status = game_instance.get("init_status", "idle")
    if current_status == "in_progress":
        raise HTTPException(status_code=400, detail="Game is already initializing")

    run_config = RunConfig(**_model_to_dict(req))
    game_instance["run_config"] = _model_to_dict(run_config)
    apply_runtime_content_locale(run_config.content_locale)

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


@app.get("/api/game/current-run")
def get_current_run():
    """获取当前运行中的开局配置快照。"""
    return _model_to_dict(get_runtime_run_config())


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

    # 为不同目标类型构建结构化详情
    if target_type == "sect":
        # 宗门详情交给专门的装配器处理，避免领域对象直接依赖 server.main
        return build_sect_detail(target, world, language_manager)

    # 其他类型继续沿用各自的领域层 get_structured_info 实现
    return target.get_structured_info()

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
                if uses_space_separated_names(language_manager.current):
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

@app.post("/api/settings/llm/test")
def test_llm_connection(req: LLMSettingsUpdate):
    """测试 LLM 连接"""
    try:
        profile, api_key = get_settings_service().get_llm_test_payload(req)
        config = LLMConfig(
            base_url=profile.base_url,
            api_key=api_key,
            model_name=profile.model_name,
        )

        success, error_msg = test_connectivity(config=config)

        if success:
            return {"status": "ok", "message": "连接成功"}
        raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试出错: {str(e)}")

@app.put("/api/settings/llm")
async def save_llm_config(req: LLMSettingsUpdate):
    """保存 LLM 配置"""
    try:
        updated = get_settings_service().update_llm(req)

        if game_instance.get("llm_check_failed", False):
            print("Detected previous LLM connection failure, resuming Simulator...")
            game_instance["llm_check_failed"] = False
            game_instance["llm_error_message"] = ""
            game_instance["is_paused"] = False
            print("Simulator resumed")
            await manager.broadcast({
                "type": "game_reinitialized",
                "message": "LLM 配置成功，游戏已恢复运行"
            })

        return {"status": "ok", "message": "配置已保存", "config": _model_to_dict(updated)}
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
            "playthrough_id": meta.get("playthrough_id", ""),
            "is_auto_save": meta.get("is_auto_save", False),
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
                
                await manager.broadcast({
                    "type": "toast",
                    "level": "info",
                    "message": t("Syncing language setting: {lang}...", lang=save_lang),
                })

                await asyncio.sleep(0.2)
                
                if save_lang != current_lang:
                    print(f"[Auto-Switch] Switching backend language from {current_lang} to {save_lang}...")
                    await asyncio.to_thread(apply_runtime_content_locale, save_lang)
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
        game_instance["run_config"] = getattr(new_world, "run_config_snapshot", _model_to_dict(get_settings_service().get_default_run_config()))

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

def _patch_sys_streams():
    """修复无控制台模式下 sys.stdout/stderr 为 None 导致 uvicorn 报错的问题"""
    import sys
    class DummyStream:
        def write(self, *args, **kwargs): pass
        def flush(self, *args, **kwargs): pass
        def isatty(self): return False
        
    if sys.stdout is None:
        sys.stdout = DummyStream()
    if sys.stderr is None:
        sys.stderr = DummyStream()

def start():
    """启动服务的入口函数"""
    _patch_sys_streams()
    import webbrowser

    # 从环境变量或配置文件读取服务器配置。
    host = os.environ.get("SERVER_HOST") or getattr(getattr(CONFIG, "system", None), "host", None) or "127.0.0.1"
    port = int(os.environ.get("SERVER_PORT") or getattr(getattr(CONFIG, "system", None), "port", None) or 8002)

    # 计算目标 URL (与 lifespan 中的逻辑保持一致)
    target_url = f"http://{host}:{port}"
    if IS_DEV_MODE:
        import socket
        def get_free_port(start_port: int, max_port: int = 65535) -> int:
            for p in range(start_port, max_port + 1):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.bind(('', p)) # Bind to all interfaces to accurately simulate what Vite does
                    s.close()
                    return p
                except OSError:
                    pass
            return start_port
            
        free_port = get_free_port(5173)
        os.environ["VITE_PORT"] = str(free_port)
        target_url = f"http://localhost:{free_port}"
        
        # 调试输出确认后端解析出的目标URL
        print(f"[Debug] Detected free port for Vite: {free_port}")
        print(f"[Debug] Target URL set to: {target_url}")

    print(f"Opening browser at {target_url}...")
    try:
        webbrowser.open(target_url)
    except Exception as e:
        print(f"Failed to open browser: {e}")
    
    # 在主线程中运行 uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start()
