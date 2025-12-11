/**
 * 地形生成相关的过程生成算法
 * 用于解决纯随机带来的视觉杂乱问题
 */

/**
 * 伪随机数生成器 (基于坐标)
 * 返回 [0, 1] 之间的浮点数
 */
function random(x: number, y: number): number {
    const dot = x * 12.9898 + y * 78.233;
    const sin = Math.sin(dot);
    return (sin * 43758.5453) % 1; // frac
}

/**
 * 获取基于噪声聚类的地块变体索引
 * 
 * 算法逻辑：
 * 1. 使用双重正弦波生成低频噪声（Biomes/群落感），让相邻的格子倾向于选择索引相近的变体。
 * 2. 叠加高频 Hash 扰动（Jitter），避免纹理过于死板或出现明显的人工波纹。
 * 3. 最终效果：变体会在地图上呈现自然的"斑块状"分布，而非杂乱的噪点。
 * 
 * @param x 地图 X 坐标
 * @param y 地图 Y 坐标
 * @param count 变体总数 (例如 9)
 * @param startIndex 变体索引起始值，默认为 0
 * @returns startIndex 到 startIndex + count - 1 之间的整数索引
 */
export function getClusteredTileVariant(x: number, y: number, count: number, startIndex: number = 0): number {
    if (count <= 1) return startIndex;

    // 1. 低频噪声 (Large Scale Noise)
    // 决定区域的主色调。Scale 越小，斑块越大。
    // 0.15 意味着大约 2PI / 0.15 ~= 40 格一个完整周期，
    // 视觉上大约 10-20 格为一个明显的"群落"。
    const scale = 0.15;
    
    // 使用两个不同频率和方向的波叠加，打破完美的对角线感
    const lowFreqNoise = Math.sin(x * scale + y * scale * 0.5) + 
                         Math.cos(y * scale * 0.8 - x * scale * 0.3);
    
    // lowFreqNoise 范围约为 [-2, 2]，归一化到 [0, 1]
    const normalizedNoise = (lowFreqNoise + 2) / 4;

    // 2. 高频扰动 (Jitter)
    // 如果完全依赖低频噪声，变体变化会像等高线一样生硬（1->2->3...）。
    // 引入扰动可以让边缘交错，且让同一群落内部也有少许变化。
    // range: [-0.5, 0.5]
    const noiseVal = Math.abs(random(x, y)); // 0~1
    const jitter = (noiseVal - 0.5) * 0.5;   // 强度系数 0.5

    // 3. 混合计算
    let finalValue = normalizedNoise + jitter;
    
    // 钳制到 [0, 1]
    finalValue = Math.max(0, Math.min(1, finalValue));

    // 4. 映射到 [startIndex, startIndex + count - 1]
    let index = Math.floor(finalValue * count) + startIndex;
    
    // 边界保护 (防止浮点误差导致溢出)
    const maxIndex = startIndex + count - 1;
    if (index > maxIndex) index = maxIndex;
    if (index < startIndex) index = startIndex;

    return index;
}

