import { describe, it, expect } from 'vitest'
import { GRADE_COLORS, getEntityColor } from '@/utils/theme'
import type { EffectEntity } from '@/types/core'

describe('theme', () => {
  describe('GRADE_COLORS', () => {
    it('should have purple colors for upper grade items', () => {
      expect(GRADE_COLORS['上品']).toBe('#c488fd')
      expect(GRADE_COLORS['宝物']).toBe('#c488fd')
      expect(GRADE_COLORS['SR']).toBe('#c488fd')
      expect(GRADE_COLORS['Upper']).toBe('#c488fd')
    })

    it('should have green colors for middle grade items', () => {
      expect(GRADE_COLORS['中品']).toBe('#88fdc4')
      expect(GRADE_COLORS['R']).toBe('#88fdc4')
      expect(GRADE_COLORS['Middle']).toBe('#88fdc4')
    })

    it('should have gold colors for artifact grade items', () => {
      expect(GRADE_COLORS['法宝']).toBe('#fddc88')
      expect(GRADE_COLORS['SSR']).toBe('#fddc88')
      expect(GRADE_COLORS['Artifact']).toBe('#fddc88')
    })

    it('should have default color', () => {
      expect(GRADE_COLORS['Default']).toBe('#cccccc')
    })

    it('should have realm colors', () => {
      expect(GRADE_COLORS['练气']).toBe('#cccccc')
      expect(GRADE_COLORS['筑基']).toBe('#88fdc4')
      expect(GRADE_COLORS['金丹']).toBe('#c488fd')
      expect(GRADE_COLORS['元婴']).toBe('#fddc88')
    })
  })

  describe('getEntityColor', () => {
    it('should return undefined for null entity', () => {
      expect(getEntityColor(null)).toBeUndefined()
    })

    it('should return undefined for undefined entity', () => {
      expect(getEntityColor(undefined)).toBeUndefined()
    })

    it('should return undefined for empty entity', () => {
      expect(getEntityColor({})).toBeUndefined()
    })

    describe('RGB array color', () => {
      it('should convert RGB array to rgb string', () => {
        const entity: Partial<EffectEntity> = {
          color: [255, 128, 64]
        }
        expect(getEntityColor(entity)).toBe('rgb(255,128,64)')
      })

      it('should handle RGB array with zeros', () => {
        const entity: Partial<EffectEntity> = {
          color: [0, 0, 0]
        }
        expect(getEntityColor(entity)).toBe('rgb(0,0,0)')
      })

      it('should ignore array with wrong length', () => {
        const entity = {
          color: [255, 128] as any
        }
        expect(getEntityColor(entity)).toBeUndefined()
      })
    })

    describe('string color', () => {
      it('should return string color directly', () => {
        const entity: Partial<EffectEntity> = {
          color: '#ff0000'
        }
        expect(getEntityColor(entity)).toBe('#ff0000')
      })

      it('should return named color directly', () => {
        const entity: Partial<EffectEntity> = {
          color: 'red'
        }
        expect(getEntityColor(entity)).toBe('red')
      })
    })

    describe('grade-based color', () => {
      it('should return color based on grade', () => {
        const entity: Partial<EffectEntity> = {
          grade: '上品'
        }
        expect(getEntityColor(entity)).toBe('#c488fd')
      })

      it('should return color based on rarity when no grade', () => {
        const entity: Partial<EffectEntity> = {
          rarity: 'SR'
        }
        expect(getEntityColor(entity)).toBe('#c488fd')
      })

      it('should prefer grade over rarity', () => {
        const entity: Partial<EffectEntity> = {
          grade: '上品',
          rarity: '中品'
        }
        expect(getEntityColor(entity)).toBe('#c488fd')
      })

      it('should match partial grade strings', () => {
        const entity: Partial<EffectEntity> = {
          grade: '上品丹药'
        }
        expect(getEntityColor(entity)).toBe('#c488fd')
      })

      it('should return undefined for unknown grade', () => {
        const entity: Partial<EffectEntity> = {
          grade: 'unknown'
        }
        expect(getEntityColor(entity)).toBeUndefined()
      })
    })

    describe('priority', () => {
      it('should prefer RGB array over grade', () => {
        const entity: Partial<EffectEntity> = {
          color: [100, 200, 150],
          grade: '上品'
        }
        expect(getEntityColor(entity)).toBe('rgb(100,200,150)')
      })

      it('should prefer string color over grade', () => {
        const entity: Partial<EffectEntity> = {
          color: '#custom',
          grade: '上品'
        }
        expect(getEntityColor(entity)).toBe('#custom')
      })
    })
  })
})
