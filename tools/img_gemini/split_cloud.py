import os
import numpy as np
from PIL import Image, ImageFilter, ImageChops

def split_cloud_smart():
    input_path = os.path.join(os.path.dirname(__file__), 'origin', 'cloud.jpg')
    output_dir = os.path.join(os.path.dirname(__file__), 'clouds')
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Processing {input_path}...")
    
    try:
        img = Image.open(input_path).convert("RGBA")
    except Exception as e:
        print(f"Error opening image: {e}")
        return

    # 1. 智能采样背景色 (Smart Sampling)
    # 取图像四周边缘的像素来计算背景特征，比只取一个角更稳健
    width, height = img.size
    # 提取上、下、左、右四条边的像素
    top_edge = np.array(img.crop((0, 0, width, 1)))
    bottom_edge = np.array(img.crop((0, height-1, width, height)))
    left_edge = np.array(img.crop((0, 0, 1, height)))
    right_edge = np.array(img.crop((width-1, 0, width, height)))
    
    # 合并边缘像素
    edges = np.concatenate([
        top_edge.reshape(-1, 4), 
        bottom_edge.reshape(-1, 4), 
        left_edge.reshape(-1, 4), 
        right_edge.reshape(-1, 4)
    ])
    
    # 计算背景色的平均值和标准差，用于确定容差范围
    bg_mean = np.mean(edges, axis=0)
    print(f"Smart sampled background color (RGBA): {bg_mean}")

    # 2. HSV 色彩空间分离 (HSV Separation)
    # 将图片转为 HSV，利用饱和度(S)和亮度(V)来区分云(通常S低V高)和深色背景(通常S高V低)
    hsv_img = img.convert("HSV")
    hsv_data = np.array(hsv_img)
    rgb_data = np.array(img)
    
    # 提取通道
    H, S, V = hsv_data[:,:,0], hsv_data[:,:,1], hsv_data[:,:,2]
    R, G, B = rgb_data[:,:,0], rgb_data[:,:,1], rgb_data[:,:,2]
    
    # 计算 RGB 欧氏距离 (针对平均背景色)
    # 只比较 RGB 前三个通道
    diff_r = R.astype(float) - bg_mean[0]
    diff_g = G.astype(float) - bg_mean[1]
    diff_b = B.astype(float) - bg_mean[2]
    rgb_distance = np.sqrt(diff_r**2 + diff_g**2 + diff_b**2)
    
    # 定义阈值
    # RGB 容差：允许背景有一定的颜色波动
    rgb_tolerance = 60.0 
    
    # HSV 辅助判断：
    # 背景通常是深紫色：需要保护云朵(白色/灰色)，云朵的特征是低饱和度(Low S)
    # 如果一个像素离背景色有点远，但它饱和度很高且偏紫，那它可能还是背景(渐变区)
    # 如果一个像素离背景色很近，但它饱和度极低(它是灰色的云边缘)，那应该保留
    
    # 创建 Alpha Mask (0 为完全透明/背景，255 为完全不透明/云)
    # 初始 Mask：距离背景色越近，Alpha 越小
    alpha_mask = np.zeros_like(H, dtype=np.float32)
    
    # 核心逻辑：
    # 1. 主要是背景：RGB 距离 < 容差
    # 2. 渐变增强：对于边缘区域，使用 Sigmoid 函数做软过渡，而不是硬切
    
    # 归一化距离，距离越小越接近背景
    normalized_dist = np.clip(rgb_distance / rgb_tolerance, 0, 1)
    
    # 简单的线性映射翻转：距离越小(背景)，Alpha越小(透明)
    # 使用平滑函数 (Smoothstep) 让过渡更自然: 3x^2 - 2x^3
    alpha_mask = np.clip((normalized_dist - 0.2) / 0.6, 0, 1) # 0.2到0.8之间过渡
    alpha_mask = alpha_mask * alpha_mask * (3 - 2 * alpha_mask)
    
    # 3. 保护云朵核心 (Cloud Core Protection)
    # 如果像素很亮(V高)且饱和度很低(S低)，强制认为是云，设为不透明
    # 假设云是白色的，背景是深色的
    is_cloud_core = (V > 150) & (S < 60) 
    alpha_mask[is_cloud_core] = 1.0
    
    # 4. 转换回 0-255 并应用羽化
    final_alpha = (alpha_mask * 255).astype(np.uint8)
    
    # 创建蒙版图像
    mask_img = Image.fromarray(final_alpha, mode='L')
    
    # 边缘羽化 (Matte Refinement)
    # 对蒙版进行轻微模糊，消除锯齿
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1.5))
    
    # 将处理好的 Alpha 通道应用回原图
    r, g, b, a = img.split()
    img_transparent = Image.merge('RGBA', (r, g, b, mask_img))

    # 切割逻辑保持不变
    width, height = img.size
    cell_width = width // 3
    cell_height = height // 3
    
    count = 0
    for r in range(3):
        for c in range(3):
            left = c * cell_width
            top = r * cell_height
            right = left + cell_width
            bottom = top + cell_height
            
            cell = img_transparent.crop((left, top, right, bottom))
            
            output_filename = f"cloud_{count}.png"
            output_path = os.path.join(output_dir, output_filename)
            cell.save(output_path)
            print(f"Saved {output_path}")
            count += 1
            
    print("Smart split done!")

if __name__ == "__main__":
    split_cloud_smart()
