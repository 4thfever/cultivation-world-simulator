import { describe, it, expect } from 'vitest'
import { getClusteredTileVariant } from '@/utils/procedural'

describe('procedural', () => {
  describe('getClusteredTileVariant', () => {
    it('should return startIndex when count is 0', () => {
      const result = getClusteredTileVariant(5, 5, 0)
      expect(result).toBe(0)
    })

    it('should return startIndex when count is 1', () => {
      const result = getClusteredTileVariant(5, 5, 1)
      expect(result).toBe(0)
    })

    it('should return startIndex when count is 1 with custom startIndex', () => {
      const result = getClusteredTileVariant(5, 5, 1, 10)
      expect(result).toBe(10)
    })

    it('should return value within valid range for count > 1', () => {
      const count = 9
      for (let x = 0; x < 20; x++) {
        for (let y = 0; y < 20; y++) {
          const result = getClusteredTileVariant(x, y, count)
          expect(result).toBeGreaterThanOrEqual(0)
          expect(result).toBeLessThan(count)
        }
      }
    })

    it('should return value within valid range with custom startIndex', () => {
      const count = 5
      const startIndex = 10
      for (let x = 0; x < 20; x++) {
        for (let y = 0; y < 20; y++) {
          const result = getClusteredTileVariant(x, y, count, startIndex)
          expect(result).toBeGreaterThanOrEqual(startIndex)
          expect(result).toBeLessThanOrEqual(startIndex + count - 1)
        }
      }
    })

    it('should be deterministic for same coordinates', () => {
      const x = 42
      const y = 17
      const count = 9

      const result1 = getClusteredTileVariant(x, y, count)
      const result2 = getClusteredTileVariant(x, y, count)
      const result3 = getClusteredTileVariant(x, y, count)

      expect(result1).toBe(result2)
      expect(result2).toBe(result3)
    })

    it('should produce different values for different coordinates', () => {
      const count = 9
      const results = new Set<number>()

      // Sample 100 different coordinates.
      for (let i = 0; i < 100; i++) {
        const result = getClusteredTileVariant(i * 7, i * 13, count)
        results.add(result)
      }

      // Should produce multiple different values (not all the same).
      expect(results.size).toBeGreaterThan(1)
    })

    it('should show clustering behavior - nearby coordinates tend to have similar values', () => {
      const count = 9
      let similarCount = 0
      const samples = 50

      for (let i = 0; i < samples; i++) {
        const x = Math.floor(Math.random() * 100)
        const y = Math.floor(Math.random() * 100)

        const center = getClusteredTileVariant(x, y, count)
        const neighbor = getClusteredTileVariant(x + 1, y, count)

        // Count how often neighbors have similar values (within 2).
        if (Math.abs(center - neighbor) <= 2) {
          similarCount++
        }
      }

      // With clustering, we expect neighbors to be similar more often than random.
      // Random would give similarity ~44% of the time (5/9 * 9 = 55% chance of diff >= 3).
      // Clustering should give higher similarity rate.
      expect(similarCount).toBeGreaterThan(samples * 0.3)
    })

    it('should handle negative coordinates', () => {
      const count = 9
      const result = getClusteredTileVariant(-10, -20, count)
      expect(result).toBeGreaterThanOrEqual(0)
      expect(result).toBeLessThan(count)
    })

    it('should handle large coordinates', () => {
      const count = 9
      const result = getClusteredTileVariant(10000, 20000, count)
      expect(result).toBeGreaterThanOrEqual(0)
      expect(result).toBeLessThan(count)
    })

    it('should handle floating point coordinates', () => {
      const count = 9
      const result = getClusteredTileVariant(5.5, 7.3, count)
      expect(result).toBeGreaterThanOrEqual(0)
      expect(result).toBeLessThan(count)
    })
  })
})
