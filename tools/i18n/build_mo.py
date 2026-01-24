#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 PO 文件编译为 MO 文件

使用方法:
    python tools/i18n/build_mo.py
"""

import subprocess
import sys
from pathlib import Path


def compile_po_to_mo(po_file: Path) -> bool:
    """编译单个 PO 文件为 MO 文件"""
    mo_file = po_file.with_suffix('.mo')
    
    try:
        # 使用 msgfmt 编译 PO 文件
        result = subprocess.run(
            ['msgfmt', '-o', str(mo_file), str(po_file)],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"[OK] {po_file.relative_to(Path.cwd())} -> {mo_file.name}")
        return True
        
    except FileNotFoundError:
        print("[ERROR] msgfmt 工具未找到。请安装 gettext 工具集。")
        print("\n安装方法:")
        print("  - Ubuntu/Debian: sudo apt-get install gettext")
        print("  - macOS: brew install gettext")
        print("  - Windows: 下载 gettext-iconv-windows 或使用 WSL")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 编译失败: {po_file}")
        if e.stderr:
            print(f"  错误信息: {e.stderr}")
        return False


def compile_po_to_mo_python(po_file: Path) -> bool:
    """使用 Python polib 库编译 PO 文件为 MO 文件（备用方案）"""
    try:
        import polib
    except ImportError:
        print("[ERROR] polib 库未安装。尝试使用 msgfmt...")
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
    
    # 尝试使用 msgfmt（推荐）
    success_count = 0
    use_msgfmt = True
    
    for po_file in po_files:
        if use_msgfmt:
            result = compile_po_to_mo(po_file)
            if not result and success_count == 0:
                # 第一次失败，尝试使用 polib
                print("\n切换到 polib 库...")
                use_msgfmt = False
                result = compile_po_to_mo_python(po_file)
        else:
            result = compile_po_to_mo_python(po_file)
        
        if result:
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
