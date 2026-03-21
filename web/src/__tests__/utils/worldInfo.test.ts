import { describe, expect, it } from 'vitest'

import { parseWorldInfoCsv, translateWorldInfoRows } from '@/utils/worldInfo'

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
        'world_info.entries.WORLD_INFO_INTRO_TITLE': 'Introduction',
        'world_info.entries.WORLD_INFO_INTRO_NAME': 'Introduction',
        'world_info.entries.WORLD_INFO_INTRO_DESC': 'This is a cultivation world where many cultivators compete.',
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
})
