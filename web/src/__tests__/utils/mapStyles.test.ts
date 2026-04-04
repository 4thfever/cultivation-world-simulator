import { describe, it, expect } from 'vitest'
import {
  getRegionTextMetrics,
  getRegionTextStyle,
  usesCompactMapLabels
} from '@/utils/mapStyles'

describe('mapStyles', () => {
  describe('usesCompactMapLabels', () => {
    it('should treat zh and ja as compact-script locales', () => {
      expect(usesCompactMapLabels('zh-CN')).toBe(true)
      expect(usesCompactMapLabels('zh-TW')).toBe(true)
      expect(usesCompactMapLabels('ja-JP')).toBe(true)
      expect(usesCompactMapLabels('en-US')).toBe(false)
    })
  })

  describe('getRegionTextMetrics', () => {
    it('should return compact metrics for zh-CN labels', () => {
      expect(getRegionTextMetrics('sect', 'zh-CN')).toEqual({
        fontSize: 64,
        lineHeight: 68,
        strokeWidth: 5
      })
      expect(getRegionTextMetrics('city', 'zh-CN')).toEqual({
        fontSize: 70,
        lineHeight: 74,
        strokeWidth: 5
      })
      expect(getRegionTextMetrics('unknown', 'zh-CN')).toEqual({
        fontSize: 68,
        lineHeight: 72,
        strokeWidth: 5
      })
    })

    it('should return latin metrics for en-US labels', () => {
      expect(getRegionTextMetrics('sect', 'en-US')).toEqual({
        fontSize: 64,
        lineHeight: 70,
        strokeWidth: 4
      })
      expect(getRegionTextMetrics('city', 'en-US')).toEqual({
        fontSize: 70,
        lineHeight: 77,
        strokeWidth: 4
      })
    })
  })

  describe('getRegionTextStyle', () => {
    it('should return compact zh-CN style for sect labels', () => {
      const style = getRegionTextStyle('sect')
      expect(style.fontFamily).toBe('"Microsoft YaHei", sans-serif')
      expect(style.fontSize).toBe(64)
      expect(style.lineHeight).toBe(68)
      expect(style.fill).toBe('#ffcc00')
      expect(style.dropShadow).toBeDefined()
      expect(style.stroke).toEqual({
        color: '#000000',
        width: 5,
        join: 'round'
      })
    })

    it('should return city style for city type', () => {
      const style = getRegionTextStyle('city')
      expect(style.fill).toBe('#ccffcc')
      expect(style.fontSize).toBe(70)
    })

    it('should return default style for unknown or empty type', () => {
      expect(getRegionTextStyle('unknown').fill).toBe('#ffffff')
      expect(getRegionTextStyle('').fill).toBe('#ffffff')
    })

    it('should adjust non-compact locale styles by locale', () => {
      const style = getRegionTextStyle('city', 'en-US')
      expect(style.fontSize).toBe(70)
      expect(style.lineHeight).toBe(77)
      expect(style.stroke).toEqual({
        color: '#000000',
        width: 4,
        join: 'round'
      })
      expect(style.dropShadow).toEqual({
        color: '#000000',
        blur: 2,
        angle: Math.PI / 6,
        distance: 2,
        alpha: 0.8
      })
    })
  })
})
