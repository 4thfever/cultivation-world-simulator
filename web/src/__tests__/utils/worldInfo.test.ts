import { describe, expect, it } from 'vitest'
import { createI18n } from 'vue-i18n'

import { parseWorldInfoCsv, translateWorldInfoRows } from '@/utils/worldInfo'
import enUSGame from '@/locales/en-US/game.json'
import jaJPGame from '@/locales/ja-JP/game.json'
import viVNGame from '@/locales/vi-VN/game.json'
import zhCNGame from '@/locales/zh-CN/game.json'
import zhTWGame from '@/locales/zh-TW/game.json'

describe('worldInfo utils', () => {
  it('parses world_info.csv rows after the two header lines', () => {
    const rows = parseWorldInfoCsv([
      'title,title_id,name_id,desc_id,desc',
      '标题,标题ID,名称ID,描述ID,描述',
      '简介,WORLD_INFO_INTRO_TITLE,WORLD_INFO_INTRO_NAME,WORLD_INFO_INTRO_DESC,这是一个诸多修士竞相修行的修仙世界。',
      '境界,WORLD_INFO_REALM_TITLE,WORLD_INFO_REALM_NAME,WORLD_INFO_REALM_DESC,修仙的境界从弱到强。',
    ].join('\n'))

    expect(rows).toEqual([
      {
        title: '简介',
        titleId: 'WORLD_INFO_INTRO_TITLE',
        nameId: 'WORLD_INFO_INTRO_NAME',
        descId: 'WORLD_INFO_INTRO_DESC',
        fallbackDesc: '这是一个诸多修士竞相修行的修仙世界。',
      },
      {
        title: '境界',
        titleId: 'WORLD_INFO_REALM_TITLE',
        nameId: 'WORLD_INFO_REALM_NAME',
        descId: 'WORLD_INFO_REALM_DESC',
        fallbackDesc: '修仙的境界从弱到强。',
      },
    ])
  })

  it('translates rows with i18n keys and falls back to csv text when missing', () => {
    const rows = [
      {
        title: '简介',
        titleId: 'WORLD_INFO_INTRO_TITLE',
        nameId: 'WORLD_INFO_INTRO_NAME',
        descId: 'WORLD_INFO_INTRO_DESC',
        fallbackDesc: '这是一个诸多修士竞相修行的修仙世界。',
      },
      {
        title: '境界',
        titleId: 'WORLD_INFO_REALM_TITLE',
        nameId: 'WORLD_INFO_REALM_NAME',
        descId: 'WORLD_INFO_REALM_DESC',
        fallbackDesc: '修仙的境界从弱到强。',
      },
    ]

    const translated = translateWorldInfoRows(rows, (key) => {
      const dictionary: Record<string, string> = {
        'game.world_info.entries.WORLD_INFO_INTRO_TITLE': 'Introduction',
        'game.world_info.entries.WORLD_INFO_INTRO_NAME': 'Introduction',
        'game.world_info.entries.WORLD_INFO_INTRO_DESC': 'This is a cultivation world where many cultivators compete.',
      }
      return dictionary[key] ?? key
    })

    expect(translated).toEqual([
      {
        id: 'WORLD_INFO_INTRO_TITLE',
        title: 'Introduction',
        name: 'Introduction',
        desc: 'This is a cultivation world where many cultivators compete.',
      },
      {
        id: 'WORLD_INFO_REALM_TITLE',
        title: '境界',
        name: '境界',
        desc: '修仙的境界从弱到强。',
      },
    ])
  })

  it('provides world info entry translations for every locale and csv row', () => {
    const rows = parseWorldInfoCsv([
      'title,title_id,name_id,desc_id,desc',
      '标题,标题ID,名称ID,描述ID,描述',
      '简介,WORLD_INFO_INTRO_TITLE,WORLD_INFO_INTRO_NAME,WORLD_INFO_INTRO_DESC,这是一个诸多修士竞相修行的修仙世界。',
      '官职,WORLD_INFO_OFFICIAL_TITLE,WORLD_INFO_OFFICIAL_NAME,WORLD_INFO_OFFICIAL_DESC,修士可为朝廷理政，积累朝廷威望并领取俸禄。',
    ].join('\n'))

    const locales = [enUSGame, zhCNGame, zhTWGame, viVNGame, jaJPGame]

    for (const locale of locales) {
      const entries = locale.world_info?.entries ?? {}
      for (const row of rows) {
        expect(entries[row.titleId]).toBeTruthy()
        expect(entries[row.nameId]).toBeTruthy()
        expect(entries[row.descId]).toBeTruthy()
      }
    }
  })

  it('uses the game namespace when resolving world info translations', () => {
    const rows = [
      {
        title: '官职',
        titleId: 'WORLD_INFO_OFFICIAL_TITLE',
        nameId: 'WORLD_INFO_OFFICIAL_NAME',
        descId: 'WORLD_INFO_OFFICIAL_DESC',
        fallbackDesc: '修士可为朝廷理政，积累朝廷威望并领取俸禄。',
      },
    ]

    const translated = translateWorldInfoRows(rows, (key) => {
      if (key === 'game.world_info.entries.WORLD_INFO_OFFICIAL_TITLE') return 'Official Rank'
      if (key === 'game.world_info.entries.WORLD_INFO_OFFICIAL_NAME') return 'Official Rank'
      if (key === 'game.world_info.entries.WORLD_INFO_OFFICIAL_DESC') return 'Cultivators may govern for the imperial court.'
      return key
    })

    expect(translated[0]).toEqual({
      id: 'WORLD_INFO_OFFICIAL_TITLE',
      title: 'Official Rank',
      name: 'Official Rank',
      desc: 'Cultivators may govern for the imperial court.',
    })
  })

  it('resolves world info translations from the real game locale namespace', () => {
    const i18n = createI18n({
      legacy: false,
      locale: 'en-US',
      messages: {
        'en-US': {
          game: enUSGame,
        },
      },
    })

    const rows = [
      {
        title: '官职',
        titleId: 'WORLD_INFO_OFFICIAL_TITLE',
        nameId: 'WORLD_INFO_OFFICIAL_NAME',
        descId: 'WORLD_INFO_OFFICIAL_DESC',
        fallbackDesc: '修士可为朝廷理政，积累朝廷威望并领取俸禄。',
      },
    ]

    const translated = translateWorldInfoRows(rows, i18n.global.t)

    expect(translated[0]?.title).toBe('Official Rank')
    expect(translated[0]?.name).toBe('Official Rank')
    expect(translated[0]?.desc).toContain('imperial court')
    expect(translated[0]?.desc).not.toContain('修士可为朝廷理政')
  })
})
