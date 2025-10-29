from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image, ImageChops, ImageFilter
from tqdm import tqdm

PathLike = Union[str, Path]



def remove_white_background(
    source: PathLike | Image.Image,
    white_threshold: int = 240,
    output: Optional[PathLike] = None,
    show_progress: bool = False,
) -> Image.Image:
    """
    移除图像中与边缘相连的白色背景，保留前景对象内部的浅色区域。
    
    使用洪水填充算法，从图像四边开始，只标记与边缘相连的接近白色的像素为背景。
    这样可以避免错误擦除前景对象内部的浅色区域。
    
    Args:
        source: 输入图像路径或 PIL Image 对象
        white_threshold: 判定白色的阈值，RGB三通道都大于此值才视为白色 (0-255)
        output: 可选的输出路径
        show_progress: 是否显示洪水填充的进度条
    
    Returns:
        处理后的 RGBA 图像，背景为透明
    """
    if isinstance(source, (str, Path)):
        with Image.open(source) as loaded:
            image = loaded.convert("RGB")
    else:
        image = source.convert("RGB")
    
    width, height = image.size
    if width == 0 or height == 0:
        result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        if output is not None:
            result.save(output)
        return result
    
    # 转换为numpy数组进行处理
    img_array = np.array(image)
    
    # 创建背景掩码，False表示前景，True表示背景
    background_mask = np.zeros((height, width), dtype=bool)
    
    # 创建访问标记
    visited = np.zeros((height, width), dtype=bool)
    
    # 洪水填充队列
    queue = deque()
    
    # 判断像素是否接近白色
    def is_white(y, x):
        pixel = img_array[y, x]
        return pixel[0] >= white_threshold and pixel[1] >= white_threshold and pixel[2] >= white_threshold
    
    # 将图像四边的白色像素加入队列
    # 上边和下边
    for x in range(width):
        if is_white(0, x):
            queue.append((0, x))
            visited[0, x] = True
            background_mask[0, x] = True
        if is_white(height - 1, x):
            queue.append((height - 1, x))
            visited[height - 1, x] = True
            background_mask[height - 1, x] = True
    
    # 左边和右边（排除角落已处理的点）
    for y in range(1, height - 1):
        if is_white(y, 0):
            queue.append((y, 0))
            visited[y, 0] = True
            background_mask[y, 0] = True
        if is_white(y, width - 1):
            queue.append((y, width - 1))
            visited[y, width - 1] = True
            background_mask[y, width - 1] = True
    
    # 洪水填充：扩展所有与边缘相连的白色区域
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    # 使用tqdm包装队列处理过程
    if show_progress:
        pbar = tqdm(total=len(queue), desc="Flood filling", unit="px")
    
    while queue:
        y, x = queue.popleft()
        
        # 检查四个方向的相邻像素
        for dy, dx in directions:
            ny, nx = y + dy, x + dx
            
            # 边界检查
            if 0 <= ny < height and 0 <= nx < width and not visited[ny, nx]:
                if is_white(ny, nx):
                    visited[ny, nx] = True
                    background_mask[ny, nx] = True
                    queue.append((ny, nx))
                    if show_progress:
                        pbar.total += 1
        
        if show_progress:
            pbar.update(1)
    
    if show_progress:
        pbar.close()
    
    # 创建RGBA图像
    result_array = np.zeros((height, width, 4), dtype=np.uint8)
    result_array[:, :, :3] = img_array  # 复制RGB通道
    result_array[:, :, 3] = np.where(background_mask, 0, 255)  # 设置Alpha通道
    
    result = Image.fromarray(result_array, mode="RGBA")
    
    if output is not None:
        result.save(output)
    
    return result


def crop_inner_region(
    source: PathLike | Image.Image,
    fraction: float = 1 / 16,
    output: Optional[PathLike] = None,
) -> Image.Image:
    """裁剪图像四边各 ``fraction`` 宽度/高度，默认各去除 1/16。"""

    if isinstance(source, (str, Path)):
        with Image.open(source) as loaded:
            image = loaded.convert("RGBA")
    else:
        image = source.copy()

    width, height = image.size
    if width == 0 or height == 0:
        return image

    fraction = max(0.0, min(fraction, 0.5))
    dx = int(round(width * fraction))
    dy = int(round(height * fraction))

    left = min(dx, width // 2)
    upper = min(dy, height // 2)
    right = max(width - dx, left)
    lower = max(height - dy, upper)

    cropped = image.crop((left, upper, right, lower))

    if output is not None:
        cropped.save(output)

    return cropped


def process(
    source: PathLike | Image.Image,
    *,
    crop_fraction: float = 1 / 16,
    white_threshold: int = 240,
    output: Optional[PathLike] = None,
    show_progress: bool = False,
) -> Image.Image:
    """先裁边后去白底的组合处理函数。"""

    cropped = crop_inner_region(source, fraction=crop_fraction)
    cleaned = remove_white_background(
        cropped, 
        white_threshold=white_threshold, 
        show_progress=show_progress
    )

    if output is not None:
        cleaned.save(output)

    return cleaned


def process_all(
    input_dir: PathLike = "result",
    output_dir: PathLike = "processed",
    *,
    crop_fraction: float = 1 / 16,
    white_threshold: int = 240,
    show_progress: bool = True,
    show_detail_progress: bool = False,
) -> list[Path]:
    """
    遍历目录内的图像文件，批量处理并保存到目标目录。
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        crop_fraction: 裁剪比例
        white_threshold: 白色阈值
        show_progress: 是否显示批处理进度条
        show_detail_progress: 是否显示每张图片的详细处理进度（洪水填充进度）
    """

    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    allowed_suffixes = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    files = [
        path
        for path in sorted(input_path.iterdir())
        if path.is_file() and path.suffix.lower() in allowed_suffixes
    ]

    iterator = tqdm(files, desc="Processing images") if show_progress else files
    saved_files: list[Path] = []

    for file_path in iterator:
        target = output_path / file_path.name
        process(
            file_path,
            crop_fraction=crop_fraction,
            white_threshold=white_threshold,
            output=target,
            show_progress=show_detail_progress,
        )
        saved_files.append(target)

    return saved_files

if __name__ == "__main__":
    process_all(
        input_dir="tools/img_gen/tmp/raw",
        output_dir="tools/img_gen/tmp/processed",
        crop_fraction=1 / 16,
    )