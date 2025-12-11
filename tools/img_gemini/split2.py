"""
将3x3网格图片切分为9张独立图片
基于行/列像素方差检测分隔线位置
"""

import os
from pathlib import Path
import numpy as np
from PIL import Image


def find_split_line(variance: np.ndarray, start: int, end: int) -> tuple[int, int]:
    """
    在指定区间内找到方差最小的连续区域（分隔线位置）
    返回 (line_start, line_end)
    """
    # 在区间内找最小值位置
    region = variance[start:end]
    min_idx = start + np.argmin(region)
    min_val = variance[min_idx]
    
    # 向两侧扩展，直到方差明显上升（超过最小值的3倍或绝对阈值）
    threshold = max(min_val * 3, 50)
    
    line_start = min_idx
    while line_start > 0 and variance[line_start - 1] < threshold:
        line_start -= 1
    
    line_end = min_idx
    while line_end < len(variance) - 1 and variance[line_end + 1] < threshold:
        line_end += 1
    
    return line_start, line_end + 1  # 返回左闭右开区间


def find_split_line_by_gradient(gray: np.ndarray, axis: int, start: int, end: int, is_bright_line: bool) -> tuple[int, int]:
    """
    基于梯度突变检测分隔线边界
    axis: 0=检测水平线, 1=检测垂直线
    is_bright_line: True=亮色分隔线(如白色), False=暗色分隔线(如黑色)
    """
    if axis == 0:
        means = np.mean(gray, axis=1)  # 每行的平均亮度
    else:
        means = np.mean(gray, axis=0)  # 每列的平均亮度
    
    # 计算相邻行/列的亮度差异（梯度）
    gradient = np.diff(means)
    
    # 找分隔线中心：在区间内找亮度极值
    region = means[start:end]
    if is_bright_line:
        center_idx = start + np.argmax(region)  # 亮色线找最亮点
    else:
        center_idx = start + np.argmin(region)  # 暗色线找最暗点
    
    # 从中心向左找边界：寻找梯度符号变化点（亮度突变）
    line_start = center_idx
    for i in range(center_idx - 1, max(0, center_idx - 30), -1):
        # 对于亮色线：边界处 gradient > 0（从暗到亮）
        # 对于暗色线：边界处 gradient < 0（从亮到暗）
        if is_bright_line and gradient[i] > 3:
            line_start = i + 1
            break
        elif not is_bright_line and gradient[i] < -3:
            line_start = i + 1
            break
        line_start = i
    
    # 从中心向右找边界
    line_end = center_idx
    for i in range(center_idx, min(len(gradient), center_idx + 30)):
        if is_bright_line and gradient[i] < -3:
            line_end = i + 1
            break
        elif not is_bright_line and gradient[i] > 3:
            line_end = i + 1
            break
        line_end = i + 1
    
    return line_start, line_end


def detect_split_lines_forest(image: Image.Image) -> tuple[list, list]:
    """专门处理 forest 的白色宽分隔线"""
    gray = np.array(image.convert('L'), dtype=np.float32)
    h, w = gray.shape
    
    h_line1 = find_split_line_by_gradient(gray, 0, h // 4, h // 2 + h // 8, is_bright_line=True)
    h_line2 = find_split_line_by_gradient(gray, 0, h // 2 + h // 8, 3 * h // 4, is_bright_line=True)
    
    v_line1 = find_split_line_by_gradient(gray, 1, w // 4, w // 2 + w // 8, is_bright_line=True)
    v_line2 = find_split_line_by_gradient(gray, 1, w // 2 + w // 8, 3 * w // 4, is_bright_line=True)
    
    return [h_line1, h_line2], [v_line1, v_line2]


def detect_split_lines_snow_mountain(image: Image.Image) -> tuple[list, list]:
    """专门处理 snow_mountain 的黑色细分隔线"""
    gray = np.array(image.convert('L'), dtype=np.float32)
    h, w = gray.shape
    
    h_line1 = find_split_line_by_gradient(gray, 0, h // 4, h // 2 + h // 8, is_bright_line=False)
    h_line2 = find_split_line_by_gradient(gray, 0, h // 2 + h // 8, 3 * h // 4, is_bright_line=False)
    
    v_line1 = find_split_line_by_gradient(gray, 1, w // 4, w // 2 + w // 8, is_bright_line=False)
    v_line2 = find_split_line_by_gradient(gray, 1, w // 2 + w // 8, 3 * w // 4, is_bright_line=False)
    
    return [h_line1, h_line2], [v_line1, v_line2]


def detect_split_lines(image: Image.Image) -> tuple[list, list]:
    """
    检测水平和垂直分隔线的位置
    返回 (h_lines, v_lines)，每个是 [(start1, end1), (start2, end2)]
    """
    gray = np.array(image.convert('L'), dtype=np.float32)
    h, w = gray.shape
    
    # 计算每行的方差
    row_variance = np.var(gray, axis=1)
    
    # 计算每列的方差
    col_variance = np.var(gray, axis=0)
    
    # 平滑处理，减少噪点影响
    kernel_size = 3
    row_variance = np.convolve(row_variance, np.ones(kernel_size)/kernel_size, mode='same')
    col_variance = np.convolve(col_variance, np.ones(kernel_size)/kernel_size, mode='same')
    
    # 在约 1/4~1/2 区间找第一条分隔线，1/2~3/4 区间找第二条
    h_line1 = find_split_line(row_variance, h // 4, h // 2 + h // 8)
    h_line2 = find_split_line(row_variance, h // 2 + h // 8, 3 * h // 4)
    
    v_line1 = find_split_line(col_variance, w // 4, w // 2 + w // 8)
    v_line2 = find_split_line(col_variance, w // 2 + w // 8, 3 * w // 4)
    
    return [h_line1, h_line2], [v_line1, v_line2]


def split_image(image: Image.Image, h_lines: list, v_lines: list) -> list[Image.Image]:
    """
    根据分隔线位置切分图片为9块
    """
    w, h = image.size
    
    # 计算切分边界：[0, line1_start, line1_end, line2_start, line2_end, total]
    y_bounds = [0, h_lines[0][0], h_lines[0][1], h_lines[1][0], h_lines[1][1], h]
    x_bounds = [0, v_lines[0][0], v_lines[0][1], v_lines[1][0], v_lines[1][1], w]
    
    tiles = []
    # 取索引 0, 2, 4 对应的区域（跳过分隔线区域 1, 3）
    for row_idx in [0, 2, 4]:
        for col_idx in [0, 2, 4]:
            left = x_bounds[col_idx]
            right = x_bounds[col_idx + 1]
            top = y_bounds[row_idx]
            bottom = y_bounds[row_idx + 1]
            
            tile = image.crop((left, top, right, bottom))
            tiles.append(tile)
    
    return tiles


def process_image(input_path: Path, output_dir: Path):
    """处理单张图片"""
    image = Image.open(input_path)
    name = input_path.stem
    
    # 特殊图像使用专门的检测方法
    if name == 'forest':
        h_lines, v_lines = detect_split_lines_forest(image)
    elif name == 'snow_mountain':
        h_lines, v_lines = detect_split_lines_snow_mountain(image)
    else:
        h_lines, v_lines = detect_split_lines(image)
    
    print(f"{name}: 水平分隔线 {h_lines}, 垂直分隔线 {v_lines}")
    
    # 切分
    tiles = split_image(image, h_lines, v_lines)
    
    # 保存
    for i, tile in enumerate(tiles):
        output_path = output_dir / f"{name}_{i}.png"
        tile.save(output_path)
        print(f"  保存: {output_path.name} ({tile.size[0]}x{tile.size[1]})")


def main():
    script_dir = Path(__file__).parent
    input_dir = script_dir / "origin2"
    output_dir = script_dir / "split2"
    
    output_dir.mkdir(exist_ok=True)
    
    # 支持的图片格式
    extensions = {'.jpg', '.jpeg', '.png'}
    
    for path in sorted(input_dir.iterdir()):
        if path.suffix.lower() in extensions:
            process_image(path, output_dir)
    
    print(f"\n完成！输出目录: {output_dir}")


if __name__ == "__main__":
    main()

