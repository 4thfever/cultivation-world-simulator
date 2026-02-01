import pytest
from src.utils.df import load_game_configs
from src.i18n import t

def test_all_csv_ids_have_translations():
    """
    遍历加载的所有游戏配置 CSV，检查所有以 _id 结尾的字段（如 name_id, desc_id, title_id），
    确保它们在中文环境下都有对应的翻译。
    
    如果 t(key) 返回的结果等于 key 本身，且 key 是全大写（典型的 ID 格式），则视为缺失翻译。
    """
    # 1. 加载配置 (force_chinese_language fixture 已经在 session 级别生效)
    configs = load_game_configs()
    
    missing_keys = []
    
    # 需要检查的 ID 后缀
    target_suffixes = ('_id', '_ID')
    # 一些已知的例外或不需要翻译的字段可以加在这里
    ignored_keys = set() 

    # 2. 遍历所有配置表
    for config_name, rows in configs.items():
        if not rows:
            continue
            
        print(f"Checking config: {config_name}.csv ({len(rows)} rows)")
        
        for i, row in enumerate(rows):
            # 遍历行中的所有键值对
            for key, value in row.items():
                # 检查 Key 是否以 _id 结尾 (例如 title_id)
                # 并且 Value 是字符串且非空
                if key.lower().endswith("id") and isinstance(value, str) and value.strip():
                    # 也可以进一步过滤，例如只检查全大写的 Value，或者特定前缀
                    # 这里假设所有需要翻译的 ID 都是全大写且包含下划线
                    if value.isupper() and "_" in value:
                        translated = t(value)
                        
                        # 如果翻译结果和原文一样，且原文不是空的，视为缺失
                        # 注意：有些 ID 本身就是英文显示（极少），这里主要针对需要转中文的情况
                        if translated == value:
                            missing_keys.append(f"[{config_name}.csv Row {i+1}] {key}={value}")

    # 3. 断言
    if missing_keys:
        error_msg = f"Found {len(missing_keys)} missing translations in zh-CN:\n" + "\n".join(missing_keys)
        pytest.fail(error_msg)
