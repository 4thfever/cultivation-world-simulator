from src.classes.sect import reload as reload_sects
from src.classes.technique import reload as reload_techniques
from src.classes.weapon import reload as reload_weapons
from src.classes.auxiliary import reload as reload_auxiliaries
from src.classes.item_registry import ItemRegistry
from src.run.log import get_logger

def reload_all_static_data():
    """
    重置所有游戏静态数据到初始状态。
    必须在每次 init_game 之前调用。
    """
    logger = get_logger().logger
    logger.info("[DataLoader] 开始重置静态游戏数据...")
    
    # 1. 清空物品注册表
    ItemRegistry.reset()
    
    # 2. 重新加载各模块数据
    # 注意顺序：有些模块可能依赖其他模块（如功法可能依赖宗门ID，虽通常只有弱引用）
    reload_sects()
    reload_techniques()
    reload_weapons() 
    reload_auxiliaries()
    
    logger.info("[DataLoader] 静态数据重置完成，环境已净化。")
