from typing import Optional, Dict


def create_font(pygame_mod, size: int, font_path: Optional[str]):
    if font_path:
        try:
            return pygame_mod.font.Font(font_path, size)
        except Exception:
            pass
    return _load_font_with_fallback(pygame_mod, size)


def _load_font_with_fallback(pygame_mod, size: int):
    candidates = [
        "Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "SimSun",
        "Consolas", "DejaVu Sans", "DejaVu Sans Mono", "Arial Unicode MS",
        "Noto Sans CJK SC", "Noto Sans CJK",
    ]
    for name in candidates:
        try:
            font = pygame_mod.font.SysFont(name, size)
            test = font.render("测试中文AaBb123", True, (255, 255, 255))
            if test.get_width() > 0:
                return font
        except Exception:
            continue
    return pygame_mod.font.SysFont(None, size)


def get_region_font(pygame_mod, cache: Dict[int, object], size: int, font_path: Optional[str]):
    if size not in cache:
        cache[size] = create_font(pygame_mod, size, font_path)
    return cache[size]


__all__ = ["create_font", "get_region_font"]


