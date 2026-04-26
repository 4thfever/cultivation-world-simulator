import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/ui'
import type { EffectEntity, SectDetail } from '@/types/core'
import { formatCultivationText } from '@/utils/cultivationText'

type DiplomacyItem = NonNullable<SectDetail['diplomacy_items']>[number]

const MAX_DIPLOMACY_ITEMS = 4

export function useSectDetailPanel(data: () => SectDetail) {
  const { t } = useI18n()
  const uiStore = useUiStore()
  const secondaryItem = ref<EffectEntity | null>(null)

  const alignmentText = computed(() => data().alignment)
  const ruleText = computed(() => data().rule_desc || t('game.info_panel.sect.no_rule'))
  const warStatusText = computed(() => (
    (data().war_summary?.active_war_count ?? 0) > 0
      ? t('game.sect_relations.status_war')
      : t('game.sect_relations.status_peace')
  ))
  const strongestEnemyText = computed(() => (
    data().war_summary?.strongest_enemy_name || t('common.none')
  ))
  const yearlyIncomeText = computed(() => (
    t('game.info_panel.sect.stats.income_value', {
      income: Math.floor(data().economy_summary?.estimated_yearly_income || 0),
    })
  ))
  const yearlyUpkeepText = computed(() => (
    t('game.info_panel.sect.stats.upkeep_value', {
      upkeep: Math.floor(data().economy_summary?.estimated_yearly_upkeep || 0),
    })
  ))
  const warWearinessText = computed(() => `${Math.max(0, Math.floor(data().war_weariness || 0))}/100`)

  const simplifiedDiplomacyItems = computed(() => {
    return [...(data().diplomacy_items ?? [])]
      .sort((a, b) => {
        if (a.status === 'war' && b.status !== 'war') return -1
        if (a.status !== 'war' && b.status === 'war') return 1
        return (a.relation_value ?? 0) - (b.relation_value ?? 0)
      })
      .slice(0, MAX_DIPLOMACY_ITEMS)
  })

  function jumpToAvatar(id: string) {
    void uiStore.select('avatar', id)
  }

  function jumpToSect(id: string) {
    void uiStore.select('sect', id)
  }

  function showDetail(item: EffectEntity | undefined) {
    if (item) {
      secondaryItem.value = item
    }
  }

  function closeSecondaryDetail() {
    secondaryItem.value = null
  }

  function getDurationYears(months: number) {
    return Math.max(0, Math.floor((months || 0) / 12))
  }

  function getDiplomacyMeta(item: DiplomacyItem) {
    const statusKey = item.status === 'war'
      ? 'game.sect_relations.status_war'
      : 'game.sect_relations.status_peace'
    const relationPart = item.relation_value === undefined
      ? ''
      : t('game.info_panel.sect.diplomacy_meta_relation', { value: item.relation_value })
    return relationPart ? `${t(statusKey)} · ${relationPart}` : t(statusKey)
  }

  function getDiplomacySub(item: DiplomacyItem) {
    const years = getDurationYears(item.duration_months)
    const durationKey = item.status === 'war'
      ? 'game.info_panel.sect.diplomacy_war_years'
      : 'game.info_panel.sect.diplomacy_peace_years'
    return t(durationKey, { count: years })
  }

  function getMemberSub(member: NonNullable<SectDetail['members']>[number]) {
    return `${formatCultivationText(member.realm, t)} · ${t('game.info_panel.avatar.stats.sect_contribution')} ${member.contribution ?? 0}`
  }

  return {
    secondaryItem,
    alignmentText,
    ruleText,
    warStatusText,
    strongestEnemyText,
    yearlyIncomeText,
    yearlyUpkeepText,
    warWearinessText,
    simplifiedDiplomacyItems,
    jumpToAvatar,
    jumpToSect,
    showDetail,
    closeSecondaryDetail,
    getDiplomacyMeta,
    getDiplomacySub,
    getMemberSub,
  }
}
