from __future__ import annotations

import argparse
import hashlib
import json
import threading
import webbrowser
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

try:
    from tools.wiki.generate import DEFAULT_OUTPUT_DIR, PROJECT_ROOT, generate
except ModuleNotFoundError:
    from generate import DEFAULT_OUTPUT_DIR, PROJECT_ROOT, generate


TOOL_ROOT = Path(__file__).resolve().parent
MANIFEST_NAME = ".wiki_manifest.json"
FINGERPRINT_VERSION = 1


def _iter_fingerprint_files() -> list[Path]:
    roots = [
        TOOL_ROOT / "index.html",
        TOOL_ROOT / "src",
        TOOL_ROOT / "generate.py",
        TOOL_ROOT / "serve.py",
        PROJECT_ROOT / "static" / "game_configs",
        PROJECT_ROOT / "static" / "locales",
        PROJECT_ROOT / "src" / "classes",
        PROJECT_ROOT / "src" / "i18n",
        PROJECT_ROOT / "src" / "utils" / "df.py",
        PROJECT_ROOT / "assets",
    ]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
            continue
        if not root.exists():
            continue
        files.extend(path for path in root.rglob("*") if path.is_file())
    return sorted(set(files), key=lambda path: path.as_posix())


def build_input_fingerprint() -> str:
    digest = hashlib.sha256()
    digest.update(f"wiki-fingerprint-v{FINGERPRINT_VERSION}\n".encode("utf-8"))
    for path in _iter_fingerprint_files():
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        stat = path.stat()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _manifest_path(output_dir: Path) -> Path:
    return output_dir / MANIFEST_NAME


def read_manifest(output_dir: Path) -> dict[str, object]:
    path = _manifest_path(output_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def write_manifest(output_dir: Path, *, input_hash: str, generated_locales: list[str]) -> None:
    payload = {
        "version": FINGERPRINT_VERSION,
        "input_hash": input_hash,
        "generated_locales": generated_locales,
    }
    _manifest_path(output_dir).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def needs_regeneration(output_dir: Path, *, input_hash: str) -> bool:
    if not (output_dir / "index.html").exists():
        return True
    if not (output_dir / "data" / "registry.json").exists():
        return True
    manifest = read_manifest(output_dir)
    return manifest.get("version") != FINGERPRINT_VERSION or manifest.get("input_hash") != input_hash


def ensure_generated(output_dir: Path, *, force: bool = False) -> tuple[bool, list[str]]:
    output_dir = output_dir.resolve()
    input_hash = build_input_fingerprint()
    if force or needs_regeneration(output_dir, input_hash=input_hash):
        generated_locales = generate(output_dir)
        write_manifest(output_dir, input_hash=input_hash, generated_locales=generated_locales)
        return True, generated_locales
    manifest = read_manifest(output_dir)
    generated_locales = [str(locale) for locale in manifest.get("generated_locales", [])]
    return False, generated_locales


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate when needed, serve, and open the cultivation wiki locally.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind. Defaults to 8765.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory. Defaults to tools/wiki/dist.")
    parser.add_argument("--force", action="store_true", help="Regenerate before serving even if inputs look unchanged.")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser automatically.")
    args = parser.parse_args()

    output_dir = args.out.resolve()
    regenerated, locales = ensure_generated(output_dir, force=args.force)
    if regenerated:
        print(f"Generated wiki for {len(locales)} locale(s): {', '.join(locales)}")
    else:
        print("Wiki is up to date; using existing generated files.")

    handler = partial(SimpleHTTPRequestHandler, directory=str(output_dir))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}/"

    if not args.no_open:
        threading.Timer(0.2, lambda: webbrowser.open(url)).start()

    print(f"Serving HTTP on {args.host} port {args.port} ({url}) ...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping wiki server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
