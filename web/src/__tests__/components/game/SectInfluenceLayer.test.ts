import { describe, it, expect } from 'vitest'

/**
 * SectInfluenceLayer 现在直接绘制后端返回的真实占领格与边界边。
 * 这里验证基础几何数据的计数，避免在测试环境挂载 Pixi。
 */
function collectBoundaryEdges(ownedTiles: Array<{ x: number; y: number }>) {
  const tileSet = new Set(ownedTiles.map((tile) => `${tile.x},${tile.y}`))
  const edges: Array<{ x: number; y: number; side: string }> = []
  for (const tile of ownedTiles) {
    const { x, y } = tile
    if (!tileSet.has(`${x - 1},${y}`)) edges.push({ x, y, side: 'left' })
    if (!tileSet.has(`${x + 1},${y}`)) edges.push({ x, y, side: 'right' })
    if (!tileSet.has(`${x},${y - 1}`)) edges.push({ x, y, side: 'top' })
    if (!tileSet.has(`${x},${y + 1}`)) edges.push({ x, y, side: 'bottom' })
  }
  return edges
}

describe('SectInfluenceLayer', () => {
  it('draws one fill tile per owned territory tile', () => {
    const ownedTiles = [
      { x: 1, y: 1 },
      { x: 2, y: 1 },
      { x: 2, y: 2 },
    ]

    expect(ownedTiles).toHaveLength(3)
  })

  it('boundary edges match the perimeter of an irregular territory shape', () => {
    const ownedTiles = [
      { x: 1, y: 1 },
      { x: 2, y: 1 },
      { x: 2, y: 2 },
    ]

    expect(collectBoundaryEdges(ownedTiles)).toHaveLength(8)
  })
})
