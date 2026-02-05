#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 PO 文件编译为 MO 文件

使用方法:
    python tools/i18n/build_mo.py
"""

import sys
from pathlib import Path


def compile_po_to_mo(po_file: Path) -> bool:
    """使用 Python polib 库编译 PO 文件为 MO 文件"""
    try:
        import polib
    except ImportError:
        print("[ERROR] polib 库未安装。请运行 pip install polib 安装。")
        return False
    
    mo_file = po_file.with_suffix('.mo')
    
    try:
        po = polib.pofile(str(po_file))
        po.save_as_mofile(str(mo_file))
        print(f"[OK] {po_file.relative_to(Path.cwd())} -> {mo_file.name}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 编译失败: {po_file}")
        print(f"  错误信息: {e}")
        return False


def main():
    """主函数：查找所有 PO 文件并编译为 MO 文件"""
    print("="*60)
    print("编译 PO 文件为 MO 文件")
    print("="*60)
    
    # 查找项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    i18n_dir = project_root / "src" / "i18n" / "locales"
    
    if not i18n_dir.exists():
        print(f"[ERROR] 找不到 i18n 目录: {i18n_dir}")
        sys.exit(1)
    
    # 查找所有 PO 文件
    po_files = list(i18n_dir.rglob("*.po"))
    
    if not po_files:
        print(f"[WARNING] 未找到 PO 文件")
        sys.exit(0)
    
    print(f"\n找到 {len(po_files)} 个 PO 文件:")
    for po_file in po_files:
        print(f"  - {po_file.relative_to(project_root)}")
    
    print("\n开始编译...")
    print("-"*60)
    
    success_count = 0
    
    for po_file in po_files:
        if compile_po_to_mo(po_file):
            success_count += 1
    
    # 输出结果
    print("-"*60)
    print(f"\n编译完成: {success_count}/{len(po_files)} 成功")
    
    if success_count == len(po_files):
        print("\n[OK] 所有 PO 文件已成功编译为 MO 文件")
        return 0
    else:
        print(f"\n[WARNING] {len(po_files) - success_count} 个文件编译失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
