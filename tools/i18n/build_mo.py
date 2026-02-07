#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 PO 文件编译为 MO 文件，支持模块化 PO 文件合并

使用方法:
    python tools/i18n/build_mo.py

功能:
    1. 扫描 src/i18n/locales 下的语言目录
    2. 支持多套模块合并逻辑:
       - modules/ -> LC_MESSAGES/messages.po
       - game_configs_modules/ -> LC_MESSAGES/game_configs.po
    3. 编译生成对应的 .mo 文件
    4. 自动编译其他独立的 .po 文件
"""

import sys
import shutil
from pathlib import Path

def compile_domain_modules(lang_dir: Path, source_folder: str, domain_name: str) -> bool:
    """
    通用函数：合并 source_folder 下的 po 文件 -> LC_MESSAGES/{domain_name}.po
    
    Args:
        lang_dir: 语言目录根路径
        source_folder: 模块源文件夹名 (如 "modules")
        domain_name: 目标域名 (如 "messages" -> messages.po)
        
    Returns:
        bool: 是否成功 (或不需要处理)
    """
    try:
        import polib
    except ImportError:
        print("[ERROR] polib 库未安装。请运行 pip install polib 安装。")
        return False
        
    modules_dir = lang_dir / source_folder
    lc_messages_dir = lang_dir / "LC_MESSAGES"
    lc_messages_dir.mkdir(parents=True, exist_ok=True)
    
    target_po_path = lc_messages_dir / f"{domain_name}.po"
    target_mo_path = lc_messages_dir / f"{domain_name}.mo"
    
    # 1. 检查模块目录是否存在
    if modules_dir.exists() and list(modules_dir.glob("*.po")):
        print(f"  [合并] {source_folder}/ -> {domain_name}.po")
        
        merged_po = polib.POFile()
        module_files = sorted(list(modules_dir.glob("*.po")))
        
        # 尝试保留 metadata
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
                    merged_po.append(entry)
                count += 1
            except Exception as e:
                print(f"    [警告] 读取 {po_file.name} 失败: {e}")
                
        print(f"    - 合并了 {count} 个文件，共 {len(merged_po)} 条目")
        
        # 保存 PO
        merged_po.save(str(target_po_path))
        
        # 编译 MO
        merged_po.save_as_mofile(str(target_mo_path))
        print(f"    - 生成: {target_mo_path.name}")
        return True
        
    # 2. 如果没有模块目录，检查是否已存在目标 PO 文件（传统模式）
    elif target_po_path.exists():
        print(f"  [编译] {domain_name}.po (无模块源)")
        try:
            po = polib.pofile(str(target_po_path))
            po.save_as_mofile(str(target_mo_path))
            return True
        except Exception as e:
            print(f"    [错误] {e}")
            return False
            
    return True # 不需要处理也不算错

def process_language(lang_dir: Path) -> bool:
    """处理单个语言目录的所有构建任务"""
    
    # 任务列表: (源文件夹, 目标文件名)
    tasks = [
        ("modules", "messages"),
        ("game_configs_modules", "game_configs")
    ]
    
    # 记录已处理的文件名，避免后续重复编译
    processed_domains = set()
    
    success = True
    
    # 1. 执行模块合并任务
    for source_folder, domain_name in tasks:
        if compile_domain_modules(lang_dir, source_folder, domain_name):
            processed_domains.add(domain_name)
        else:
            success = False
            
    # 2. 扫描并编译其他未处理的独立 PO 文件
    lc_messages_dir = lang_dir / "LC_MESSAGES"
    if lc_messages_dir.exists():
        for po_file in lc_messages_dir.glob("*.po"):
            domain = po_file.stem
            if domain in processed_domains:
                continue
                
            print(f"  [编译] {po_file.name} (独立文件)")
            try:
                import polib
                po = polib.pofile(str(po_file))
                po.save_as_mofile(str(po_file.with_suffix('.mo')))
            except Exception as e:
                print(f"    [错误] {e}")
                
    return success

def main():
    print("="*60)
    print("构建 i18n 文件 (Module -> PO -> MO)")
    print("="*60)
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    i18n_dir = project_root / "static" / "locales"
    
    if not i18n_dir.exists():
        print(f"[ERROR] 找不到 i18n 目录: {i18n_dir}")
        sys.exit(1)
    
    all_success = True
    for lang_dir in i18n_dir.iterdir():
        if not lang_dir.is_dir() or lang_dir.name == "templates":
            continue
            
        print(f"\n处理语言: {lang_dir.name}")
        if not process_language(lang_dir):
            all_success = False
            
    print("-" * 60)
    if all_success:
        print("\n[OK] 所有语言包构建完成")
        return 0
    else:
        print("\n[FAIL] 构建过程中出现错误")
        return 1

if __name__ == "__main__":
    sys.exit(main())
