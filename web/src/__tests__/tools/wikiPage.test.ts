import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

describe('wiki tool page', () => {
  it('exposes the static shell and script entry', () => {
    const html = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'index.html'), 'utf-8')

    expect(html).toContain('id="localeSelect"')
    expect(html).toContain('id="globalSearchInput"')
    expect(html).toContain('id="tabs"')
    expect(html).toContain('src="./src/app.js"')
    expect(html).toContain('href="./src/styles.css"')
    expect(html).not.toContain('id="searchInput"')
    expect(html).not.toContain('id="rarityFilterSelect"')
  })

  it('renders image-aware wiki card styles', () => {
    const css = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'src', 'styles.css'), 'utf-8')
    const js = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'src', 'app.js'), 'utf-8')

    expect(css).toContain('.card-cover')
    expect(css).toContain('.image-gallery')
    expect(css).toContain('color-scheme: dark')
    expect(css).toContain('.theme-rarity-ssr')
    expect(js).toContain('normalizeImageList')
    expect(js).toContain('renderImage')
    expect(js).toContain('renderTabFilters')
    expect(js).toContain("'title_id'")
    expect(js).toContain('fieldRequirements')
    expect(js).not.toContain('fieldTheme')
    expect(js).toContain("'effect_desc'")
  })

  it('hides internal color fields and renders array relations as chips', () => {
    const js = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'src', 'app.js'), 'utf-8')

    expect(js).toContain("'color'")
    expect(js).toContain('Array.isArray(item.value)')
    expect(js).toContain('item.value.map((value) => ({ key: value, label: value }))')
  })

  it('keeps select controls wide enough to show option labels', () => {
    const css = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'src', 'styles.css'), 'utf-8')

    expect(css).toContain('min-width: 132px')
    expect(css).toContain('width: 100%')
  })

  it('renders tab-scoped search, rarity, and realm filters inside content', () => {
    const css = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'src', 'styles.css'), 'utf-8')
    const js = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'src', 'app.js'), 'utf-8')

    expect(css).toContain('.tab-filters')
    expect(js).toContain('function availableRealms(tab)')
    expect(js).toContain('function matchesRealmFilter(item)')
    expect(js).toContain('id="searchInput"')
    expect(js).toContain('id="rarityFilterSelect"')
    expect(js).toContain('id="realmFilterSelect"')
    expect(js).toContain('matchesRealmFilter(item)')
  })

  it('lists item, resource, hidden domain, and sect task tabs independently', () => {
    const js = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'src', 'app.js'), 'utf-8')

    expect(js).toContain("'weapons'")
    expect(js).toContain("'auxiliaries'")
    expect(js).toContain("'elixirs'")
    expect(js).toContain("'materials'")
    expect(js).toContain("'animals'")
    expect(js).toContain("'plants'")
    expect(js).toContain("'lodes'")
    expect(js).toContain("'hidden_domains'")
    expect(js).toContain("'sect_tasks'")
    expect(js).toContain("sect_tasks: '宗门任务'")
    expect(js).toContain("hidden_domains: '秘境'")
  })

  it('renders grouped wiki tabs when groups are plain arrays', () => {
    const js = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'src', 'app.js'), 'utf-8')

    expect(js).toContain('function groupItems(group)')
    expect(js).toContain('if (Array.isArray(group)) return group')
    expect(js).toContain('Object.values(tab.items).flatMap(groupItems)')
    expect(js).toContain('const items = groupItems(group)')
    expect(js).toContain('const count = allTabItems(tab).length')
  })

  it('documents the local build and serve flow', () => {
    const readme = readFileSync(resolve(process.cwd(), '..', 'tools', 'wiki', 'README.md'), 'utf-8')

    expect(readme).toContain('python tools/wiki/serve.py')
    expect(readme).toContain('regenerates `tools/wiki/dist` only when')
    expect(readme).toContain('http://127.0.0.1:8765')
  })
})
