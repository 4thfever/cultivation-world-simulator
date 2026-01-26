import { describe, it, expect } from 'vitest'
import { formatHp, formatAge } from '@/utils/formatters/number'

describe('formatters/number', () => {
  describe('formatHp', () => {
    it('should format integer HP values', () => {
      expect(formatHp(100, 200)).toBe('100 / 200')
    })

    it('should floor decimal current HP', () => {
      expect(formatHp(99.7, 200)).toBe('99 / 200')
      expect(formatHp(99.2, 200)).toBe('99 / 200')
    })

    it('should handle full HP', () => {
      expect(formatHp(100, 100)).toBe('100 / 100')
    })

    it('should handle zero HP', () => {
      expect(formatHp(0, 100)).toBe('0 / 100')
    })

    it('should handle large HP values', () => {
      expect(formatHp(12345, 99999)).toBe('12345 / 99999')
    })

    it('should handle negative HP', () => {
      expect(formatHp(-10, 100)).toBe('-10 / 100')
    })
  })

  describe('formatAge', () => {
    it('should format age and lifespan', () => {
      expect(formatAge(25, 100)).toBe('25 / 100')
    })

    it('should handle zero age', () => {
      expect(formatAge(0, 100)).toBe('0 / 100')
    })

    it('should handle age equal to lifespan', () => {
      expect(formatAge(100, 100)).toBe('100 / 100')
    })

    it('should handle large age values', () => {
      expect(formatAge(1000, 5000)).toBe('1000 / 5000')
    })

    it('should handle age exceeding lifespan', () => {
      expect(formatAge(150, 100)).toBe('150 / 100')
    })
  })
})
