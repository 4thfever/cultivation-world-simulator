export interface Point {
  x: number
  y: number
}

interface PositionedObject {
  id: string
  x: number
  y: number
}

/**
 * 计算角色在格子内的视觉偏移量，避免重叠
 * @param items 包含坐标的对象列表
 * @param radius 偏移半径（相对于格子大小的比例，0.25 表示 1/4 格子宽）
 */
export function calculateVisualOffsets<T extends PositionedObject>(
  items: T[],
  radius: number = 0.25
): Map<string, Point> {
  const groups = new Map<string, T[]>()
  const offsets = new Map<string, Point>()

  // 1. 按坐标分组
  for (const item of items) {
    const key = `${item.x},${item.y}`
    if (!groups.has(key)) {
      groups.set(key, [])
    }
    groups.get(key)!.push(item)
  }

  // 2. 计算每组的偏移
  for (const group of groups.values()) {
    const count = group.length
    
    // 只有一个人时，不需要偏移，居中显示
    if (count <= 1) {
      offsets.set(group[0].id, { x: 0, y: 0 })
      continue
    }

    // 多人时，按圆形分布
    // 无论多少人，都均匀分布在圆周上
    // 起始角度 -PI/2 (即正上方)，让排列更符合直觉
    const angleStep = (Math.PI * 2) / count
    
    group.forEach((item, index) => {
      const angle = index * angleStep - Math.PI / 2
      offsets.set(item.id, {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius
      })
    })
  }

  return offsets
}

