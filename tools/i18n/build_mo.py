#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 PO 文件编译为 MO 文件，支持模块化 PO 文件合并

使用方法:
    python tools/i18n/build_mo.py

功能:
    1. 扫描 src/i18n/locales 下的语言目录
    2. 如果存在 modules/ 目录，将所有 .po 文件合并
    3. 生成/更新 LC_MESSAGES/messages.po (作为合并后的完整文件)
    4. 编译生成 LC_MESSAGES/messages.mo
    5. 同时处理其他独立的 .po 文件 (如 game_configs.po)
"""

import sys
import shutil
from pathlib import Path

def compile_modules(lang_dir: Path) -> bool:
    """
    编译该语言目录下的模块
    
    Args:
        lang_dir: 语言目录，如 src/i18n/locales/zh_CN
        
    Returns:
        bool: 是否成功
    """
    try:
        import polib
    except ImportError:
        print("[ERROR] polib 库未安装。请运行 pip install polib 安装。")
        return False
        
    lc_messages_dir = lang_dir / "LC_MESSAGES"
    lc_messages_dir.mkdir(parents=True, exist_ok=True)
    
    modules_dir = lang_dir / "modules"
    
    # 1. 处理 messages.po (可能来自 modules 拆分，也可能就是单个文件)
    if modules_dir.exists() and list(modules_dir.glob("*.po")):
        print(f"  [合并] 发现模块化文件: {lang_dir.name}/modules/ -> messages.po")
        
        # 创建一个新的 PO 对象
        merged_po = polib.POFile()
        
        # 收集所有模块文件
        module_files = sorted(list(modules_dir.glob("*.po")))
        
        # 为了保留 metadata，尝试先读取 common.po 或 misc.po，或者直接从第一个文件读
        # 最好是如果你有专门的 header.po，这里我们直接用第一个文件的 metadata
        if module_files:
            try:
                first_po = polib.pofile(str(module_files[0]))
                merged_po.metadata = first_po.metadata
            except:
                pass
                
        # 遍历合并
        count = 0
        for po_file in module_files:
            try:
                po = polib.pofile(str(po_file))
                for entry in po:
                    # 检查是否重复 (简单去重)
                    # 注意：如果 key 重复，polib 默认可能不会报错，但这里我们 append
                    # 真实场景可能需要 merge 逻辑，这里假设 modules 之间无交集
                    merged_po.append(entry)
                count += 1
            except Exception as e:
                print(f"    [警告] 读取 {po_file.name} 失败: {e}")
                
        print(f"    - 合并了 {count} 个文件，共 {len(merged_po)} 条目")
        
        # 保存合并后的 messages.po (方便查看和作为中间文件)
        merged_po_path = lc_messages_dir / "messages.po"
        merged_po.save(str(merged_po_path))
        
        # 编译为 MO
        merged_mo_path = lc_messages_dir / "messages.mo"
        merged_po.save_as_mofile(str(merged_mo_path))
        print(f"    - 生成: {merged_mo_path.name}")
        
    else:
        # 没有 modules，尝试直接编译现有的 messages.po
        legacy_po = lc_messages_dir / "messages.po"
        if legacy_po.exists():
            print(f"  [编译] {lang_dir.name}/messages.po")
            try:
                po = polib.pofile(str(legacy_po))
                po.save_as_mofile(str(legacy_po.with_suffix('.mo')))
            except Exception as e:
                print(f"    [错误] {e}")
                return False

    # 2. 处理其他独立的 PO 文件 (如 game_configs.po)
    # 只要不是 messages.po (上面已经处理过)，都单独编译
    for po_file in lc_messages_dir.glob("*.po"):
        if po_file.name == "messages.po":
            continue
            
        print(f"  [编译] {po_file.name}")
        try:
            po = polib.pofile(str(po_file))
            po.save_as_mofile(str(po_file.with_suffix('.mo')))
        except Exception as e:
            print(f"    [错误] {e}")
            
    return True

def main():
    print("="*60)
    print("构建 i18n 文件 (Module -> PO -> MO)")
    print("="*60)
    
    # 查找项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    i18n_dir = project_root / "static" / "locales"
    
    if not i18n_dir.exists():
        print(f"[ERROR] 找不到 i18n 目录: {i18n_dir}")
        sys.exit(1)
    
    # 遍历语言目录
    success = True
    for lang_dir in i18n_dir.iterdir():
        if not lang_dir.is_dir() or lang_dir.name == "templates":
            continue
            
        print(f"\n处理语言: {lang_dir.name}")
        if not compile_modules(lang_dir):
            success = False
            
    print("-" * 60)
    if success:
        print("\n[OK] 所有语言包构建完成")
        return 0
    else:
        print("\n[FAIL] 构建过程中出现错误")
        return 1

if __name__ == "__main__":
    sys.exit(main())
