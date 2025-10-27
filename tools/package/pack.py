from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent


def run(cmd: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(cmd, cwd=str(cwd or PROJECT_ROOT), capture_output=True, text=True, shell=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    return proc.stdout.strip()


def get_current_tag() -> str:
    # 优先使用当前 tag；若没有打 tag，则用短 commit id
    try:
        tag = run(["git", "describe", "--tags", "--exact-match"]).strip()
        if tag:
            return tag
    except Exception:
        pass
    # 回退到当前 commit 短哈希
    try:
        short = run(["git", "rev-parse", "--short", "HEAD"]).strip()
        return f"commit-{short}"
    except Exception:
        return "untagged"


def read_git_ignored_paths() -> set[str]:
    """
    读取 .gitignore（若存在）并返回需忽略的模式集合（简单前缀/目录名过滤）。
    我们只用于资源复制时的粗过滤；最终以 PyInstaller 的 --exclude/--add-data 控制。
    """
    ignored: set[str] = set()
    gi = PROJECT_ROOT / ".gitignore"
    if not gi.exists():
        return ignored
    for line in gi.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        ignored.add(s)
    return ignored


def is_path_ignored(path: Path, ignored_patterns: set[str]) -> bool:
    # 仅用简单规则过滤常见目录：logs、台本、cache、__pycache__、*.log、TODO、*.md 临时内容等
    name = path.name
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    if name in {"logs", "台本", "cache", "__pycache__"}:
        return True
    if name.lower() in {"todo"}:
        return True
    if rel.startswith("tools/package/"):
        return True
    if any(seg == "__pycache__" for seg in path.parts):
        return True
    if path.suffix.lower() in {".log"}:
        return True
    # 粗略匹配 .gitignore 的以目录结尾的规则
    for pat in ignored_patterns:
        if pat.endswith("/") and rel.startswith(pat.rstrip("/")):
            return True
        if pat == rel or rel.startswith(pat.rstrip("/")):
            # 简化：若规则与开头匹配，则跳过
            return True
    return False


def build_with_pyinstaller(output_dir: Path) -> None:
    # 入口脚本
    entry = PROJECT_ROOT / "src" / "run" / "run.py"

    # 资源目录：assets 与 static（排除 static/local_config.yml）
    add_data_args: list[str] = []
    assets_dir = PROJECT_ROOT / "assets"
    static_dir = PROJECT_ROOT / "static"
    tmp_dir = output_dir / "_tmp_resources"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    if assets_dir.exists():
        add_data_args += ["--add-data", f"{assets_dir}{os.pathsep}assets"]
    if static_dir.exists():
        # 构建一个不包含 local_config.yml 的临时 static 目录
        tmp_static = tmp_dir / "static"
        if tmp_static.exists():
            shutil.rmtree(tmp_static)
        shutil.copytree(static_dir, tmp_static)
        lc = tmp_static / "local_config.yml"
        if lc.exists():
            lc.unlink()
        add_data_args += ["--add-data", f"{tmp_static}{os.pathsep}static"]

    # 额外的排除（减少包体）
    exclude_modules = [
        "tests",
        "unittest",
        "tkinter",
        "pytest",
        "matplotlib",
    ]
    exclude_args: list[str] = []
    for m in exclude_modules:
        exclude_args += ["--exclude-module", m]

    # 运行 PyInstaller（优先单目录，兼容资源文件；不开启 --onefile 以避免 pygame 资源路径问题）
    dist_dir = output_dir
    build_dir = output_dir / "build"
    spec_path = output_dir
    build_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--name", "cultivation-world-simulator",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(spec_path),
        "--console",
        # 去掉调试与符号，减小体积
        "--optimize", "2",
        # 隐式集合数据（若依赖包有数据）
        "--collect-all", "omegaconf",
        "--collect-all", "json5",
        "--collect-submodules", "pygame",
    ] + exclude_args + add_data_args + [str(entry)]

    print("[1/3] 调用 PyInstaller...")
    print("命令:", " ".join(cmd))
    run(cmd)
    print("PyInstaller 完成。")


def copy_project_side_files(output_dir: Path, tag_name: str) -> None:
    print("[2/3] 复制说明与许可证...")
    app_dir = output_dir / "cultivation-world-simulator"
    app_dir.mkdir(parents=True, exist_ok=True)

    # 将 README、LICENSE、requirements.txt 复制到应用目录，便于分发
    for fname in ["README.md", "EN_README.md", "LICENSE", "requirements.txt"]:
        src = PROJECT_ROOT / fname
        if src.exists():
            dst = app_dir / fname
            shutil.copy2(src, dst)

    # 生成一个运行说明
    (app_dir / "HOW_TO_RUN.txt").write_text(
        (
            "运行说明:\n"
            "1) 双击 cultivation-world-simulator/cultivation-world-simulator.exe 启动\n"
            "2) 如需配置 LLM，请编辑 static/config.yml 或在外部同目录提供 static/local_config.yml 覆盖\n"
            f"版本: {tag_name}\n"
        ),
        encoding="utf-8",
    )


def _copy_env_installer(app_dir: Path) -> None:
    print("[3/3] 放置用户安装脚本...")
    src_cmd = TOOLS_DIR / "set_env.cmd"
    if src_cmd.exists():
        # 复制到 exe 同目录，并重命名
        dst_cmd = app_dir / "启动前点击安装.exe"
        try:
            shutil.copy2(src_cmd, dst_cmd)
        except Exception as e:
            print(f"警告：复制 set_env.cmd 失败：{e}")
    else:
        print("提示：未找到 tools/package/set_env.cmd，跳过复制。")


def main() -> None:
    tag = get_current_tag()
    # 输出改为项目根 tmp/{tag}
    release_dir = PROJECT_ROOT / "tmp" / tag

    # 清理旧目录
    if release_dir.exists():
        print(f"清理旧目录: {release_dir}")
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    build_with_pyinstaller(release_dir)
    copy_project_side_files(release_dir, tag)
    _copy_env_installer(release_dir / "cultivation-world-simulator")

    # 删除多余：构建中间产物
    build_dir = release_dir / "build"
    spec_file = release_dir / "cultivation-world-simulator.spec"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if spec_file.exists():
        spec_file.unlink()
    # 删除临时资源
    tmp_dir = release_dir / "_tmp_resources"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    # 确保没有把 gitignore 指定的目录带入（单目录输出仅包含 PyInstaller 产物与我们复制的文件）
    ignored = read_git_ignored_paths()
    for path in release_dir.rglob("*"):
        if is_path_ignored(path, ignored):
            if path.is_file():
                try:
                    path.unlink()
                except Exception:
                    pass
            else:
                try:
                    shutil.rmtree(path)
                except Exception:
                    pass

    print(f"打包完成: {release_dir}")


if __name__ == "__main__":
    main()


