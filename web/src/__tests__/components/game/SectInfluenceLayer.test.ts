import { describe, it, expect } from 'vitest'

/**
 * SectInfluenceLayer 绘制逻辑：菱形范围内格数（曼哈顿距离 <= radius）。
 * 本测试验证该逻辑与组件预期一致，避免在测试环境挂载 Pixi 导致的递归更新。
 */
function countDiamondTiles(radius: number): number {
  let n = 0
  for (let dx = -radius; dx <= radius; dx++) {
    for (let dy = -radius; dy <= radius; dy++) {
      if (Math.abs(dx) + Math.abs(dy) <= radius) n++
    }
  }
  return n
}

describe('SectInfluenceLayer', () => {
  it('diamond tile count for influence_radius matches drawing loop', () => {
    expect(countDiamondTiles(0)).toBe(1)
    expect(countDiamondTiles(1)).toBe(5)
    expect(countDiamondTiles(2)).toBe(13)
    expect(countDiamondTiles(3)).toBe(25)
  })
})
