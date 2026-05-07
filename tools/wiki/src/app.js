const state = {
  registry: null,
  data: null,
  locale: '',
  tab: '',
  query: '',
  globalQuery: '',
  rarityFilter: '',
  realmFilter: '',
  targetHash: '',
}

const tabOrder = [
  'world',
  'actions',
  'personas',
  'sects',
  'sect_tasks',
  'orthodoxies',
  'races',
  'techniques',
  'weapons',
  'auxiliaries',
  'elixirs',
  'materials',
  'animals',
  'plants',
  'lodes',
  'hidden_domains',
  'regions',
]

const messages = {
  'zh-CN': {
    appTitle: '修仙世界 Wiki',
    loading: '正在加载资料...',
    language: '语言 / Language',
    tabSearch: '当前页搜索',
    tabSearchPlaceholder: '搜索当前 tab',
    globalSearch: '全局搜索',
    globalSearchPlaceholder: '搜索所有 tab',
    noMatchingRecords: '没有匹配的资料。',
    noTabSelected: '未选择 tab。',
    failedToLoad: 'Wiki 资料加载失败：{message}',
    dataWarnings: '资料警告',
    details: '详情',
    incomplete: '资料不完整',
    missing: '缺失',
    records: '条资料',
    yes: '是',
    no: '否',
    untitled: '未命名',
    fieldId: 'ID',
    fieldType: '类型',
    fieldDesc: '描述',
    fieldEffect: '效果',
    fieldRequirements: '要求',
    rarityFilter: '稀有度',
    allRarities: '全部稀有度',
    realmFilter: '境界',
    allRealms: '全部境界',
    tabs: {
      world: '世界信息',
      actions: '动作',
      personas: '特质',
      sects: '宗门',
      sect_tasks: '宗门任务',
      orthodoxies: '道统',
      races: '种族',
      techniques: '功法',
      weapons: '武器',
      auxiliaries: '法宝',
      elixirs: '丹药',
      materials: '材料',
      animals: '动物',
      plants: '植物',
      lodes: '矿脉',
      hidden_domains: '秘境',
      regions: '区域',
    },
    themes: {
      'rarity-n': '普通',
      'rarity-r': '稀有',
      'rarity-sr': '超稀有',
      'rarity-ssr': '传说',
      'grade-lower': '下品',
      'grade-middle': '中品',
      'grade-upper': '上品',
      'grade-qi': '练气',
      'grade-foundation': '筑基',
      'grade-core': '金丹',
      'grade-nascent': '元婴',
      'race-human': '人族',
      'race-yao': '妖族',
      domain: '秘境',
      'sect-task': '宗门任务',
    },
  },
  'zh-TW': {
    appTitle: '修仙世界 Wiki',
    loading: '正在載入資料...',
    language: '語言 / Language',
    tabSearch: '目前頁搜尋',
    tabSearchPlaceholder: '搜尋目前 tab',
    globalSearch: '全域搜尋',
    globalSearchPlaceholder: '搜尋所有 tab',
    noMatchingRecords: '沒有符合的資料。',
    noTabSelected: '未選擇 tab。',
    failedToLoad: 'Wiki 資料載入失敗：{message}',
    dataWarnings: '資料警告',
    details: '詳情',
    incomplete: '資料不完整',
    missing: '缺失',
    records: '筆資料',
    yes: '是',
    no: '否',
    untitled: '未命名',
    fieldId: 'ID',
    fieldType: '類型',
    fieldDesc: '描述',
    fieldEffect: '效果',
    fieldRequirements: '要求',
    rarityFilter: '稀有度',
    allRarities: '全部稀有度',
    realmFilter: '境界',
    allRealms: '全部境界',
    tabs: {
      world: '世界資訊',
      actions: '動作',
      personas: '特質',
      sects: '宗門',
      sect_tasks: '宗門任務',
      orthodoxies: '道統',
      races: '種族',
      techniques: '功法',
      weapons: '武器',
      auxiliaries: '法寶',
      elixirs: '丹藥',
      materials: '材料',
      animals: '動物',
      plants: '植物',
      lodes: '礦脈',
      hidden_domains: '秘境',
      regions: '區域',
    },
    themes: {
      'rarity-n': '普通',
      'rarity-r': '稀有',
      'rarity-sr': '超稀有',
      'rarity-ssr': '傳說',
      'grade-lower': '下品',
      'grade-middle': '中品',
      'grade-upper': '上品',
      'grade-qi': '練氣',
      'grade-foundation': '築基',
      'grade-core': '金丹',
      'grade-nascent': '元嬰',
      'race-human': '人族',
      'race-yao': '妖族',
      domain: '秘境',
      'sect-task': '宗門任務',
    },
  },
  'en-US': {
    appTitle: 'Cultivation World Wiki',
    loading: 'Loading data...',
    language: 'Language',
    tabSearch: 'Tab Search',
    tabSearchPlaceholder: 'Search current tab',
    globalSearch: 'Global Search',
    globalSearchPlaceholder: 'Search all tabs',
    noMatchingRecords: 'No matching records.',
    noTabSelected: 'No tab selected.',
    failedToLoad: 'Failed to load wiki data: {message}',
    dataWarnings: 'Data warnings',
    details: 'Details',
    incomplete: 'Incomplete',
    missing: 'Missing',
    records: 'records',
    yes: 'Yes',
    no: 'No',
    untitled: 'Untitled',
    fieldId: 'ID',
    fieldType: 'Type',
    fieldDesc: 'Description',
    fieldEffect: 'Effect',
    fieldRequirements: 'Requirements',
    rarityFilter: 'Rarity',
    allRarities: 'All rarities',
    realmFilter: 'Realm',
    allRealms: 'All realms',
    tabs: {
      world: 'World Info',
      actions: 'Actions',
      personas: 'Persona',
      sects: 'Sects',
      sect_tasks: 'Sect Tasks',
      orthodoxies: 'Orthodoxies',
      races: 'Races',
      techniques: 'Techniques',
      weapons: 'Weapons',
      auxiliaries: 'Auxiliaries',
      elixirs: 'Elixirs',
      materials: 'Materials',
      animals: 'Animals',
      plants: 'Plants',
      lodes: 'Lodes',
      hidden_domains: 'Hidden Domains',
      regions: 'Regions',
    },
    themes: {
      'rarity-n': 'Common',
      'rarity-r': 'Rare',
      'rarity-sr': 'Super Rare',
      'rarity-ssr': 'Legendary',
      'grade-lower': 'Lower Grade',
      'grade-middle': 'Middle Grade',
      'grade-upper': 'Upper Grade',
      'grade-qi': 'Qi Refining',
      'grade-foundation': 'Foundation',
      'grade-core': 'Golden Core',
      'grade-nascent': 'Nascent Soul',
      'race-human': 'Human',
      'race-yao': 'Yao',
      domain: 'Hidden Domain',
      'sect-task': 'Sect Task',
    },
  },
  'vi-VN': {
    appTitle: 'Wiki Thế Giới Tu Tiên',
    loading: 'Đang tải dữ liệu...',
    language: 'Ngôn ngữ / Language',
    tabSearch: 'Tìm trong tab',
    tabSearchPlaceholder: 'Tìm trong tab hiện tại',
    globalSearch: 'Tìm toàn cục',
    globalSearchPlaceholder: 'Tìm trong mọi tab',
    noMatchingRecords: 'Không có dữ liệu phù hợp.',
    noTabSelected: 'Chưa chọn tab.',
    failedToLoad: 'Không tải được dữ liệu wiki: {message}',
    dataWarnings: 'Cảnh báo dữ liệu',
    details: 'Chi tiết',
    incomplete: 'Chưa đầy đủ',
    missing: 'Thiếu',
    records: 'bản ghi',
    yes: 'Có',
    no: 'Không',
    untitled: 'Chưa đặt tên',
    fieldId: 'ID',
    fieldType: 'Loại',
    fieldDesc: 'Mô tả',
    fieldEffect: 'Hiệu ứng',
    fieldRequirements: 'Yêu cầu',
    rarityFilter: 'Độ hiếm',
    allRarities: 'Tất cả độ hiếm',
    realmFilter: 'Cảnh giới',
    allRealms: 'Tất cả cảnh giới',
    tabs: {
      world: 'Thông tin thế giới',
      actions: 'Hành động',
      personas: 'Đặc chất',
      sects: 'Tông môn',
      sect_tasks: 'Nhiệm vụ tông môn',
      orthodoxies: 'Đạo thống',
      races: 'Chủng tộc',
      techniques: 'Công pháp',
      weapons: 'Vũ khí',
      auxiliaries: 'Pháp bảo',
      elixirs: 'Đan dược',
      materials: 'Vật liệu',
      animals: 'Linh thú',
      plants: 'Linh thực',
      lodes: 'Mạch khoáng',
      hidden_domains: 'Bí cảnh',
      regions: 'Khu vực',
    },
    themes: {
      'rarity-n': 'Thường',
      'rarity-r': 'Hiếm',
      'rarity-sr': 'Siêu hiếm',
      'rarity-ssr': 'Truyền thuyết',
      'grade-lower': 'Hạ phẩm',
      'grade-middle': 'Trung phẩm',
      'grade-upper': 'Thượng phẩm',
      'grade-qi': 'Luyện Khí',
      'grade-foundation': 'Trúc Cơ',
      'grade-core': 'Kim Đan',
      'grade-nascent': 'Nguyên Anh',
      'race-human': 'Nhân tộc',
      'race-yao': 'Yêu tộc',
      domain: 'Bí cảnh',
      'sect-task': 'Nhiệm vụ tông môn',
    },
  },
  'ja-JP': {
    appTitle: '修仙世界 Wiki',
    loading: 'データを読み込み中...',
    language: '言語 / Language',
    tabSearch: 'タブ内検索',
    tabSearchPlaceholder: '現在のタブを検索',
    globalSearch: '全体検索',
    globalSearchPlaceholder: 'すべてのタブを検索',
    noMatchingRecords: '一致する資料がありません。',
    noTabSelected: 'タブが選択されていません。',
    failedToLoad: 'Wiki データの読み込みに失敗しました: {message}',
    dataWarnings: 'データ警告',
    details: '詳細',
    incomplete: '未完成',
    missing: '不足',
    records: '件',
    yes: 'はい',
    no: 'いいえ',
    untitled: '無題',
    fieldId: 'ID',
    fieldType: '種類',
    fieldDesc: '説明',
    fieldEffect: '効果',
    fieldRequirements: '要件',
    rarityFilter: 'レア度',
    allRarities: 'すべてのレア度',
    realmFilter: '境界',
    allRealms: 'すべての境界',
    tabs: {
      world: '世界情報',
      actions: '行動',
      personas: '特質',
      sects: '宗門',
      sect_tasks: '宗門任務',
      orthodoxies: '道統',
      races: '種族',
      techniques: '功法',
      weapons: '武器',
      auxiliaries: '法宝',
      elixirs: '丹薬',
      materials: '素材',
      animals: '霊獣',
      plants: '霊植',
      lodes: '鉱脈',
      hidden_domains: '秘境',
      regions: '地域',
    },
    themes: {
      'rarity-n': '通常',
      'rarity-r': 'レア',
      'rarity-sr': 'スーパーレア',
      'rarity-ssr': '伝説',
      'grade-lower': '下品',
      'grade-middle': '中品',
      'grade-upper': '上品',
      'grade-qi': '練気',
      'grade-foundation': '築基',
      'grade-core': '金丹',
      'grade-nascent': '元嬰',
      'race-human': '人族',
      'race-yao': '妖族',
      domain: '秘境',
      'sect-task': '宗門任務',
    },
  },
}

const $ = (selector) => document.querySelector(selector)

function localeMessages() {
  return messages[state.locale] || messages['en-US']
}

function msg(key, replacements = {}) {
  const value = localeMessages()[key] ?? messages['en-US'][key] ?? key
  return Object.entries(replacements).reduce(
    (text, [name, replacement]) => text.replace(`{${name}}`, String(replacement)),
    value,
  )
}

function tabLabel(key) {
  return localeMessages().tabs?.[key] || messages['en-US'].tabs[key] || key
}

function themeLabel(key) {
  return localeMessages().themes?.[key] || messages['en-US'].themes[key] || key
}

function applyShellMessages() {
  document.querySelectorAll('[data-i18n]').forEach((element) => {
    element.textContent = msg(element.dataset.i18n)
  })
  document.querySelectorAll('[data-i18n-placeholder]').forEach((element) => {
    element.setAttribute('placeholder', msg(element.dataset.i18nPlaceholder))
  })
}

async function fetchJson(path) {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`Failed to load ${path}: ${response.status}`)
  }
  return response.json()
}

function readHash() {
  const params = new URLSearchParams(location.hash.replace(/^#/, ''))
  return {
    locale: params.get('lang') || '',
    tab: params.get('tab') || '',
    query: params.get('q') || '',
    globalQuery: params.get('gq') || '',
    rarityFilter: params.get('rarity') || '',
    realmFilter: params.get('realm') || '',
  }
}

function writeHash() {
  const params = new URLSearchParams()
  if (state.locale) params.set('lang', state.locale)
  if (state.tab) params.set('tab', state.tab)
  if (state.query) params.set('q', state.query)
  if (state.globalQuery) params.set('gq', state.globalQuery)
  if (state.rarityFilter) params.set('rarity', state.rarityFilter)
  if (state.realmFilter) params.set('realm', state.realmFilter)
  history.replaceState(null, '', `#${params.toString()}`)
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function textOf(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  return JSON.stringify(value)
}

function normalizeImageList(item) {
  const images = []
  if (item.cover_image && item.cover_image.src) {
    images.push(item.cover_image)
  }
  if (Array.isArray(item.images)) {
    item.images.forEach((image) => {
      if (image && image.src && !images.some((entry) => entry.src === image.src)) {
        images.push(image)
      }
    })
  }
  return images
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') return ''
  if (typeof value === 'boolean') return value ? msg('yes') : msg('no')
  if (Array.isArray(value)) return value.map(formatValue).filter(Boolean).join(', ')
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

function matchesQuery(item, query) {
  if (!query) return true
  return textOf(item).toLowerCase().includes(query.toLowerCase())
}

function getCardTheme(item) {
  return item.theme || item.rarity?.level || item.meta?.tone || ''
}

function getRarityLevel(item) {
  const level = item.rarity?.level || item.rarity
  return typeof level === 'string' ? level.toUpperCase() : ''
}

function getThemeLabel(item) {
  const theme = getCardTheme(item)
  return themeLabel(theme)
}

function themeClass(item) {
  const theme = getCardTheme(item)
  return theme ? `theme-${theme}` : ''
}

function buildDetailRows(item) {
  const hiddenDetailKeys = new Set([
    'id',
    'name',
    'title',
    'type',
    'type_name',
    'grade',
    'desc',
    'effect_desc',
    'color',
    'title_id',
    'name_id',
    'desc_id',
    'requirements',
    'meta',
    'completeness',
    'theme',
  ])
  return Object.entries(item)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .filter(([key]) => !hiddenDetailKeys.has(key))
    .map(([key, value]) => {
      const formatted = formatValue(value)
      const isBlock = formatted.includes('\n') || formatted.length > 120
      const isRelationList = key === 'relations' || key === 'techniques'
      const isImageField = key === 'cover_image' || key === 'images'
      const rows = isImageField
        ? buildImageGallery(value)
        : isRelationList && value && typeof value === 'object'
        ? buildRelationChips(value)
        : `<dd class="${isBlock ? 'block-value' : ''}">${escapeHtml(formatted)}</dd>`

      return `
        <div class="field">
          <dt>${escapeHtml(key)}</dt>
          ${rows}
        </div>
      `
    })
    .join('')
}

function buildImageGallery(value) {
  const images = normalizeImageList({ images: Array.isArray(value) ? value : [value] })
  if (!images.length) {
    return '<dd class="muted">-</dd>'
  }
  return `<dd class="image-gallery">${images.map(renderImage).join('')}</dd>`
}

function renderImage(image) {
  return `
    <figure class="image-frame">
      <img src="${escapeHtml(image.src)}" alt="${escapeHtml(image.alt || '')}" loading="lazy" />
      ${image.alt ? `<figcaption>${escapeHtml(image.alt)}</figcaption>` : ''}
    </figure>
  `
}

function buildRelationChips(value) {
  const items = Array.isArray(value)
    ? value
    : Object.entries(value).map(([key, relationValue]) => ({
        key,
        value: relationValue,
      }))

  if (!items.length) {
    return '<dd class="muted">-</dd>'
  }

  const chips = items
    .flatMap((item) => {
      if (Array.isArray(item.value)) {
        return item.value.map((value) => ({ key: value, label: value }))
      }
      const key = item.id || item.name || item.value || item.key || ''
      const label = item.name || item.value || item.id || item
      return [{ key, label }]
    })
    .filter((item) => item.label)
    .map((item) => {
      const target = String(item.key || item.label).toLowerCase()
      return `<button class="chip" type="button" data-jump="${escapeHtml(target)}">${escapeHtml(item.label)}</button>`
    })
    .join('')

  return `<dd class="chips">${chips}</dd>`
}

function pickSummary(item) {
  return [
    [msg('fieldId'), item.id],
    [msg('fieldType'), item.type_name || item.type || item.grade],
    [msg('fieldDesc'), item.desc],
    [msg('fieldEffect'), item.effect_desc],
    [msg('fieldRequirements'), item.requirements],
  ].filter(([, value]) => value !== undefined && value !== null && value !== '')
}

function renderMetaBar(item) {
  const completeness = item.completeness || { complete: true, missing: [] }
  const warnings = []
  if (!completeness.complete) warnings.push(`${msg('missing')}: ${completeness.missing.join(', ')}`)
  if (!warnings.length) {
    return ''
  }
  return `
    <div class="meta-bar">
      ${warnings.map((warning) => `<span>${escapeHtml(warning)}</span>`).join('')}
    </div>
  `
}

function renderCard(item) {
  const details = buildDetailRows(item)
  const title = item.name || item.title || item.id || msg('untitled')
  const subtitle = [item.type_name || item.type || item.grade].filter(Boolean).join(' · ')
  const summary = pickSummary(item)
    .map(([key, value]) => `<span><b>${escapeHtml(key)}</b> ${escapeHtml(formatValue(value))}</span>`)
    .join('')
  const warning = item.completeness && !item.completeness.complete
    ? `<div class="warning">${escapeHtml(msg('incomplete'))}: ${escapeHtml(item.completeness.missing.join(', '))}</div>`
    : ''
  const images = normalizeImageList(item)
  const cover = images[0]
  const detailsBlock = details
    ? `
      <details>
        <summary>${escapeHtml(msg('details'))}</summary>
        <dl>${details}</dl>
      </details>
    `
    : ''

  return `
    <article class="card ${themeClass(item)}">
      ${cover ? `<div class="card-cover">${renderImage(cover)}</div>` : ''}
      <header>
        <div>
          <h2>${escapeHtml(String(title))}</h2>
          ${subtitle ? `<p>${escapeHtml(String(subtitle))}</p>` : ''}
        </div>
      </header>
      ${renderMetaBar(item)}
      <div class="summary">${summary}</div>
      ${warning}
      ${detailsBlock}
    </article>
  `
}

function visibleTextForSearch(item) {
  const fields = [
    item.name,
    item.title,
    item.desc,
    item.effect_desc,
    item.requirements,
    item.rule_desc,
    item.orthodoxy_name,
    (item.cover_image && item.cover_image.alt) || '',
    JSON.stringify(item.images || []),
    JSON.stringify(item.relations || {}),
  ]
  return fields.filter(Boolean).join(' ').toLowerCase()
}

function matchesGlobalQuery(item, query) {
  if (!query) return true
  return visibleTextForSearch(item).includes(query.toLowerCase())
}

function matchesRarityFilter(item) {
  if (!state.rarityFilter) return true
  return getRarityLevel(item) === state.rarityFilter
}

function itemRealmValues(item) {
  const values = []
  const add = (value) => {
    if (value === null || value === undefined || value === '') return
    if (Array.isArray(value)) {
      value.forEach(add)
      return
    }
    values.push(String(value))
  }

  add(item.realm)
  add(item.required_realm)
  add(item.allowed_realms)

  if (item.grade && (item.meta?.category === 'material' || item.meta?.tone === 'resource')) {
    add(item.grade)
  }

  return [...new Set(values)]
}

function matchesRealmFilter(item) {
  if (!state.realmFilter) return true
  return itemRealmValues(item).includes(state.realmFilter)
}

function filterItems(items) {
  return items.filter(
    (item) =>
      matchesQuery(item, state.query) &&
      matchesGlobalQuery(item, state.globalQuery) &&
      matchesRarityFilter(item) &&
      matchesRealmFilter(item),
  )
}

function groupItems(group) {
  if (Array.isArray(group)) return group
  return group?.items || []
}

function allTabItems(tab) {
  if (!tab) return []
  if (tab.kind === 'groups') {
    return Object.values(tab.items).flatMap(groupItems)
  }
  return tab.items || []
}

function availableRarityLevels(tab) {
  const order = ['N', 'R', 'SR', 'SSR']
  const levels = new Set(allTabItems(tab).map(getRarityLevel).filter(Boolean))
  return order.filter((level) => levels.has(level)).concat([...levels].filter((level) => !order.includes(level)).sort())
}

function availableRealms(tab) {
  const order = ['练气', '築基', '筑基', '金丹', '元嬰', '元婴', 'Qi Refinement', 'Foundation Establishment', 'Core Formation', 'Nascent Soul']
  const levels = new Set(allTabItems(tab).flatMap(itemRealmValues).filter(Boolean))
  return order.filter((level) => levels.has(level)).concat([...levels].filter((level) => !order.includes(level)).sort())
}

function rarityOptionLabel(level) {
  return themeLabel(`rarity-${level.toLowerCase()}`)
}

function renderTabFilters(tab) {
  const rarityLevels = availableRarityLevels(tab)
  const realms = availableRealms(tab)

  if (!rarityLevels.length) {
    state.rarityFilter = ''
  }
  if (!realms.length) {
    state.realmFilter = ''
  }
  if (state.rarityFilter && !rarityLevels.includes(state.rarityFilter)) {
    state.rarityFilter = ''
  }
  if (state.realmFilter && !realms.includes(state.realmFilter)) {
    state.realmFilter = ''
  }

  return `
    <div class="tab-filters">
      <label class="control search-control">
        <span>${escapeHtml(msg('tabSearch'))}</span>
        <input id="searchInput" type="search" value="${escapeHtml(state.query)}" placeholder="${escapeHtml(msg('tabSearchPlaceholder'))}" />
      </label>
      ${
        rarityLevels.length
          ? `<label class="control">
              <span>${escapeHtml(msg('rarityFilter'))}</span>
              <select id="rarityFilterSelect">
                <option value="">${escapeHtml(msg('allRarities'))}</option>
                ${rarityLevels
                  .map(
                    (level) =>
                      `<option value="${escapeHtml(level)}" ${state.rarityFilter === level ? 'selected' : ''}>${escapeHtml(
                        rarityOptionLabel(level),
                      )}</option>`,
                  )
                  .join('')}
              </select>
            </label>`
          : ''
      }
      ${
        realms.length
          ? `<label class="control">
              <span>${escapeHtml(msg('realmFilter'))}</span>
              <select id="realmFilterSelect">
                <option value="">${escapeHtml(msg('allRealms'))}</option>
                ${realms
                  .map(
                    (realm) =>
                      `<option value="${escapeHtml(realm)}" ${state.realmFilter === realm ? 'selected' : ''}>${escapeHtml(realm)}</option>`,
                  )
                  .join('')}
              </select>
            </label>`
          : ''
      }
    </div>
  `
}

function renderList(items) {
  const filtered = filterItems(items)
  if (!filtered.length) {
    return `<p class="empty">${escapeHtml(msg('noMatchingRecords'))}</p>`
  }
  return `<div class="grid">${filtered.map(renderCard).join('')}</div>`
}

function renderGroups(groups) {
  const sections = Object.entries(groups).map(([groupKey, group]) => {
    const items = groupItems(group)
    const filtered = filterItems(items)
    return `
      <section class="group-section">
        <h2>${escapeHtml(group.title || tabLabel(groupKey))} <span>${filtered.length}</span></h2>
        ${filtered.length ? `<div class="grid">${filtered.map(renderCard).join('')}</div>` : `<p class="empty">${escapeHtml(msg('noMatchingRecords'))}</p>`}
      </section>
    `
  })
  return sections.join('')
}

function renderTabs() {
  const tabs = $('#tabs')
  tabs.innerHTML = tabOrder
    .filter((key) => state.data?.tabs?.[key])
    .map((key) => {
      const active = key === state.tab ? 'active' : ''
      return `<button class="${active}" data-tab="${key}" type="button">${tabLabel(key)}</button>`
    })
    .join('')

  tabs.querySelectorAll('button').forEach((button) => {
    button.addEventListener('click', () => {
      state.tab = button.dataset.tab
      state.query = ''
      state.rarityFilter = ''
      state.realmFilter = ''
      writeHash()
      render()
    })
  })
}

function collectCompletenessWarnings(tab) {
  const warnings = []
  const inspect = (item, path) => {
    const completeness = item.completeness
    if (completeness && !completeness.complete) {
      warnings.push(`${path} ${msg('missing')}: ${completeness.missing.join(', ')}`)
    }
  }

  if (tab.kind === 'groups') {
    Object.entries(tab.items).forEach(([groupName, group]) => {
      groupItems(group).forEach((item) => inspect(item, `${group.title || groupName}/${item.name || item.id}`))
    })
  } else {
    tab.items.forEach((item) => inspect(item, `${item.name || item.id}`))
  }

  return warnings
}

function render() {
  renderTabs()
  applyShellMessages()
  const content = $('#content')
  const tab = state.data?.tabs?.[state.tab]
  if (!tab) {
    content.innerHTML = `<p class="empty">${escapeHtml(msg('noTabSelected'))}</p>`
    return
  }

  const count = allTabItems(tab).length

  const warnings = collectCompletenessWarnings(tab)
  const warningBlock = warnings.length
    ? `<section class="global-warning"><strong>${escapeHtml(msg('dataWarnings'))}</strong><ul>${warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul></section>`
    : ''

  $('#metaLine').textContent = `${state.locale} · ${tabLabel(state.tab)} · ${count} ${msg('records')}`
  content.innerHTML = `
    <div class="section-heading">
      <h2>${tabLabel(state.tab) || tab.title}</h2>
      <span>${count} ${msg('records')}</span>
    </div>
    ${renderTabFilters(tab)}
    ${warningBlock}
    ${tab.kind === 'groups' ? renderGroups(tab.items) : renderList(tab.items)}
  `
  bindTabFilters()
  bindJumpButtons()
}

function bindTabFilters() {
  const searchInput = $('#searchInput')
  if (searchInput) {
    searchInput.addEventListener('input', (event) => {
      const cursor = event.target.selectionStart || event.target.value.length
      state.query = event.target.value
      writeHash()
      render()
      const nextInput = $('#searchInput')
      if (nextInput) {
        nextInput.focus()
        nextInput.setSelectionRange(cursor, cursor)
      }
    })
  }

  const raritySelect = $('#rarityFilterSelect')
  if (raritySelect) {
    raritySelect.addEventListener('change', (event) => {
      state.rarityFilter = event.target.value
      writeHash()
      render()
    })
  }

  const realmSelect = $('#realmFilterSelect')
  if (realmSelect) {
    realmSelect.addEventListener('change', (event) => {
      state.realmFilter = event.target.value
      writeHash()
      render()
    })
  }
}

function bindJumpButtons() {
  document.querySelectorAll('[data-jump]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.jump || ''
      if (!target) return
      state.globalQuery = target
      $('#globalSearchInput').value = target
      writeHash()
      render()
    })
  })
}

function renderLocales() {
  const select = $('#localeSelect')
  select.innerHTML = state.registry.locales
    .map((locale) => `<option value="${escapeHtml(locale.code)}">${escapeHtml(locale.label)} (${escapeHtml(locale.code)})</option>`)
    .join('')
  select.value = state.locale
  select.addEventListener('change', async () => {
    state.locale = select.value
    await loadLocale(state.locale)
    writeHash()
    render()
  })
}

async function loadLocale(locale) {
  state.data = await fetchJson(`./data/${locale}.json`)
  document.documentElement.lang = state.registry.locales.find((item) => item.code === locale)?.html_lang || 'en'
  if (!state.tab || !state.data.tabs[state.tab]) {
    state.tab = 'world'
  }
}

function attachSearchHandlers() {
  $('#globalSearchInput').value = state.globalQuery

  $('#globalSearchInput').addEventListener('input', (event) => {
    state.globalQuery = event.target.value
    writeHash()
    render()
  })
}

async function init() {
  const hash = readHash()
  state.registry = await fetchJson('./data/registry.json')
  state.locale = hash.locale || state.registry.default_locale || state.registry.locales[0].code
  state.tab = hash.tab || 'world'
  state.query = hash.query || ''
  state.globalQuery = hash.globalQuery || ''
  state.rarityFilter = hash.rarityFilter || ''
  state.realmFilter = hash.realmFilter || ''

  attachSearchHandlers()
  await loadLocale(state.locale)
  renderLocales()
  writeHash()
  render()
}

init().catch((error) => {
  console.error(error)
  $('#content').innerHTML = `<p class="empty">${escapeHtml(msg('failedToLoad', { message: error.message }))}</p>`
})
