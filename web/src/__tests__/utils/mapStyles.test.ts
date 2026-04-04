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
        fontSize: 52,
        lineHeight: 55,
        strokeWidth: 5
      })
      expect(getRegionTextMetrics('city', 'zh-CN')).toEqual({
        fontSize: 58,
        lineHeight: 61,
        strokeWidth: 5
      })
      expect(getRegionTextMetrics('unknown', 'zh-CN')).toEqual({
        fontSize: 56,
        lineHeight: 59,
        strokeWidth: 5
      })
    })

    it('should return latin metrics for en-US labels', () => {
      expect(getRegionTextMetrics('sect', 'en-US')).toEqual({
        fontSize: 52,
        lineHeight: 57,
        strokeWidth: 4
      })
      expect(getRegionTextMetrics('city', 'en-US')).toEqual({
        fontSize: 58,
        lineHeight: 64,
        strokeWidth: 4
      })
    })
  })

  describe('getRegionTextStyle', () => {
    it('should return compact zh-CN style for sect labels', () => {
      const style = getRegionTextStyle('sect')
      expect(style.fontFamily).toBe('"Microsoft YaHei", sans-serif')
      expect(style.fontSize).toBe(52)
      expect(style.lineHeight).toBe(55)
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
      expect(style.fontSize).toBe(58)
    })

    it('should return default style for unknown or empty type', () => {
      expect(getRegionTextStyle('unknown').fill).toBe('#ffffff')
      expect(getRegionTextStyle('').fill).toBe('#ffffff')
    })

    it('should adjust non-compact locale styles by locale', () => {
      const style = getRegionTextStyle('city', 'en-US')
      expect(style.fontSize).toBe(58)
      expect(style.lineHeight).toBe(64)
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
