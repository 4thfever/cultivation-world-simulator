export const STATUS_BAR_COLORS = {
  neutral: '#8c8c8c',
  worldInfo: '#78b6ff',
  ranking: '#cfa53a',
  tournament: '#cf6f3d',
  sectRelations: '#7c8ff7',
  mortal: '#5fbf7a',
  dynasty: '#b8793b',
  hiddenDomainDormant: '#6f6253',
  hiddenDomainActive: '#d8a14a',
} as const

export const PHENOMENON_RARITY_COLORS: Record<string, string> = {
  N: '#9aa4b2',
  R: '#63a3ff',
  SR: '#63c28b',
  SSR: '#e1ab52',
}

export const SHARED_UI_COLORS = {
  textPrimary: '#f3f1ec',
  textSecondary: '#c8c4ba',
  textMuted: '#90897c',
  borderSubtle: '#33302b',
  surfaceBase: 'rgba(255, 255, 255, 0.03)',
  surfaceRaised: 'rgba(255, 255, 255, 0.05)',
  linkBlue: '#78b6ff',
  linkBlueHover: '#a2cdff',
  dangerStrong: '#d48370',
  dangerSoft: '#ff7875',
  successStrong: '#88bf8b',
  successSoft: '#95de64',
  warningStrong: '#d8b35b',
} as const

export const SYSTEM_PANEL_THEMES = {
  ranking: {
    accent: STATUS_BAR_COLORS.ranking,
    accentStrong: '#f1cf6d',
    accentSoft: 'rgba(207, 165, 58, 0.16)',
    link: '#7fc0ff',
    linkHover: '#abd4ff',
    title: '#f1cf6d',
    empty: '#8f8472',
    border: '#3c3223',
  },
  tournament: {
    accent: STATUS_BAR_COLORS.tournament,
    accentStrong: '#ea9a63',
    accentSoft: 'rgba(207, 111, 61, 0.16)',
    link: '#ffb38a',
    linkHover: '#ffd0b7',
    title: '#f0bb94',
    empty: '#9a7e6d',
    border: '#4a2e24',
  },
  sectRelations: {
    accent: STATUS_BAR_COLORS.sectRelations,
    accentStrong: '#a8b4ff',
    accentSoft: 'rgba(124, 143, 247, 0.14)',
    link: '#8fa0ff',
    linkHover: '#bcc6ff',
    title: '#c8d0ff',
    empty: '#8b8ea6',
    border: '#2f3352',
  },
  mortal: {
    accent: STATUS_BAR_COLORS.mortal,
    accentStrong: '#99d7ab',
    accentSoft: 'rgba(95, 191, 122, 0.12)',
    title: '#b9e3c3',
    empty: '#7f9484',
    border: '#294032',
  },
  dynasty: {
    accent: STATUS_BAR_COLORS.dynasty,
    accentStrong: '#e1b680',
    accentSoft: 'rgba(184, 121, 59, 0.14)',
    title: '#e3c7a3',
    empty: '#978470',
    border: '#47321f',
  },
} as const
