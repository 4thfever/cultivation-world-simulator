import { describe, it, expect } from 'vitest'
import { REGION_STYLES, getRegionTextStyle } from '@/utils/mapStyles'

describe('mapStyles', () => {
  describe('REGION_STYLES', () => {
    it('should have sect style', () => {
      expect(REGION_STYLES.sect).toBeDefined()
      expect(REGION_STYLES.sect.fontSize).toBe(60)
      expect(REGION_STYLES.sect.fill).toBe('#ffcc00')
    })

    it('should have city style', () => {
      expect(REGION_STYLES.city).toBeDefined()
      expect(REGION_STYLES.city.fontSize).toBe(72)
      expect(REGION_STYLES.city.fill).toBe('#ccffcc')
    })

    it('should have default style', () => {
      expect(REGION_STYLES.default).toBeDefined()
      expect(REGION_STYLES.default.fontSize).toBe(72)
      expect(REGION_STYLES.default.fill).toBe('#ffffff')
    })

    it('should have consistent font family', () => {
      const expectedFont = '"Microsoft YaHei", sans-serif'
      expect(REGION_STYLES.sect.fontFamily).toBe(expectedFont)
      expect(REGION_STYLES.city.fontFamily).toBe(expectedFont)
      expect(REGION_STYLES.default.fontFamily).toBe(expectedFont)
    })

    it('should have drop shadow on all styles', () => {
      expect(REGION_STYLES.sect.dropShadow).toBeDefined()
      expect(REGION_STYLES.city.dropShadow).toBeDefined()
      expect(REGION_STYLES.default.dropShadow).toBeDefined()
    })
  })

  describe('getRegionTextStyle', () => {
    it('should return sect style for sect type', () => {
      const style = getRegionTextStyle('sect')
      expect(style).toBe(REGION_STYLES.sect)
    })

    it('should return city style for city type', () => {
      const style = getRegionTextStyle('city')
      expect(style).toBe(REGION_STYLES.city)
    })

    it('should return default style for default type', () => {
      const style = getRegionTextStyle('default')
      expect(style).toBe(REGION_STYLES.default)
    })

    it('should return default style for unknown type', () => {
      const style = getRegionTextStyle('unknown')
      expect(style).toBe(REGION_STYLES.default)
    })

    it('should return default style for empty string', () => {
      const style = getRegionTextStyle('')
      expect(style).toBe(REGION_STYLES.default)
    })
  })
})
