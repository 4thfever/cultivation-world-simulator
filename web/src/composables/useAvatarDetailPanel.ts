import { computed, ref } from 'vue'
import type { ComposerTranslation } from 'vue-i18n'
import type { AvatarDetail, EffectEntity, RelationInfo } from '@/types/core'
import { BloodRelationType } from '@/constants/relations'
import { avatarApi } from '@/api'
import type { useUiStore } from '@/stores/ui'
import { logError } from '@/utils/appError'
import { getAvatarPortraitUrl } from '@/utils/assetUrls'
import { formatCultivationText } from '@/utils/cultivationText'
import scrollIcon from '@/assets/icons/ui/lucide/scroll.svg'
import shieldIcon from '@/assets/icons/ui/lucide/shield.svg'
import swordsIcon from '@/assets/icons/ui/lucide/swords.svg'
import zapIcon from '@/assets/icons/ui/lucide/zap.svg'

type UiStore = ReturnType<typeof useUiStore>
export type AvatarAdjustCategory = 'technique' | 'weapon' | 'auxiliary' | 'personas' | 'goldfinger'

const ZH_NUMBERS = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']

export function parseAvatarEffectLine(line: string, t: ComposerTranslation): { source: string; segments: string[] } {
  const trimmed = line.trim()
  if (!trimmed.startsWith('[')) {
    return {
      source: t('ui.other'),
      segments: trimmed.split(/[;；]/).map(segment => segment.trim()).filter(Boolean),
    }
  }

  const separatorIndex = trimmed.lastIndexOf('] ')
  if (separatorIndex <= 0) {
    return {
      source: t('ui.other'),
      segments: [trimmed],
    }
  }

  return {
    source: trimmed.slice(1, separatorIndex).trim() || t('ui.other'),
    segments: trimmed
      .slice(separatorIndex + 2)
      .split(/[;；]/)
      .map(segment => segment.trim())
      .filter(Boolean),
  }
}

export function buildAvatarRelationMetaLines(rel: RelationInfo): string[] {
  const parts = (rel.relation || '')
    .split(/\s*\/\s*/)
    .map(part => part.trim())
    .filter(Boolean)

  let structuralParts = parts
  let attitudeText: string | null = null

  if (rel.numeric_relation && parts.length > 0) {
    attitudeText = parts[parts.length - 1]
    structuralParts = parts.slice(0, -1)
  }

  const lines: string[] = []

  if (structuralParts.length > 0) {
    lines.push(structuralParts.join(' / '))
  }

  if (attitudeText && rel.numeric_relation !== 'stranger') {
    const friendlinessSuffix = typeof rel.friendliness === 'number' ? `（${rel.friendliness}）` : ''
    lines.push(`${attitudeText}${friendlinessSuffix}`)
  }

  return lines
}

export function createMortalRelationPlaceholder(labelKey: 'father_short' | 'mother_short'): RelationInfo {
  return {
    target_id: `mortal_${labelKey}_placeholder`,
    name: '',
    relation: '',
    relation_type: BloodRelationType.TO_ME_IS_PARENT,
    blood_relation: BloodRelationType.TO_ME_IS_PARENT,
    realm: '',
    sect: '',
    is_mortal: true,
    label_key: labelKey,
  }
}

export function useAvatarDetailPanel(
  data: () => AvatarDetail,
  t: ComposerTranslation,
  locale: { value: string },
  uiStore: UiStore,
  confirmClear: (message: string) => boolean = window.confirm,
  alertError: (message: string) => void = window.alert,
) {
  const secondaryItem = ref<EffectEntity | null>(null)
  const adjustCategory = ref<AvatarAdjustCategory | null>(null)
  const showPortraitPanel = ref(false)
  const showObjectiveModal = ref(false)
  const objectiveContent = ref('')

  const currentEffectsText = computed(() => data().current_effects || data()['当前效果'])
  const currentEffectsLines = computed(() => {
    const text = currentEffectsText.value
    if (!text || text === '无') return []
    return text.split('\n')
  })

  const parsedCurrentEffects = computed(() => currentEffectsLines.value.map((line, idx) => ({
    id: `${idx}-${line}`,
    ...parseAvatarEffectLine(line, t),
  })))

  const portraitUrl = computed(() => getAvatarPortraitUrl(data().gender, data().pic_id, data().realm_id || data().realm))

  const equipmentSlots = computed(() => [
    {
      category: 'technique' as const,
      label: t('game.info_panel.avatar.adjust.categories.technique'),
      icon: scrollIcon,
      item: data().technique ?? null,
      meta: undefined,
    },
    {
      category: 'weapon' as const,
      label: t('game.info_panel.avatar.adjust.categories.weapon'),
      icon: swordsIcon,
      item: data().weapon ?? null,
      meta: data().weapon?.proficiency !== undefined
        ? t('game.info_panel.avatar.weapon_meta', { value: data().weapon?.proficiency })
        : undefined,
    },
    {
      category: 'auxiliary' as const,
      label: t('game.info_panel.avatar.adjust.categories.auxiliary'),
      icon: shieldIcon,
      item: data().auxiliary ?? null,
      meta: undefined,
    },
    {
      category: 'goldfinger' as const,
      label: t('game.info_panel.avatar.sections.goldfinger'),
      icon: zapIcon,
      item: data().goldfinger ?? null,
      meta: undefined,
    },
  ])

  const avatarHeaderSubtitle = computed(() => data().sect?.name || t('game.info_panel.avatar.stats.rogue'))
  const avatarRealmText = computed(() => formatCultivationText(data().realm, t))

  const formattedRanking = computed(() => {
    const ranking = data().ranking
    if (!ranking) return null
    const { type, rank } = ranking
    const listName = t(`game.ranking.${type}`).split(' ')[0]

    if (locale.value.startsWith('zh')) {
      return `${listName}第${ZH_NUMBERS[rank] || rank}`
    }
    if (locale.value.startsWith('ja')) {
      return `${listName}${rank}位`
    }
    return `${listName} Rank ${rank}`
  })

  const groupedRelations = computed(() => {
    const rels = data().relations || []
    const existingParents = rels.filter(rel => rel.blood_relation === BloodRelationType.TO_ME_IS_PARENT)
    const displayParents = [...existingParents]
    const hasFather = existingParents.some(parent => parent.target_gender === 'male')
    const hasMother = existingParents.some(parent => parent.target_gender === 'female')

    if (existingParents.length < 2) {
      if (!hasFather) {
        displayParents.unshift(createMortalRelationPlaceholder('father_short'))
      }
      if (!hasMother) {
        displayParents.push(createMortalRelationPlaceholder('mother_short'))
      }
    }

    const children = rels.filter(rel =>
      rel.blood_relation === BloodRelationType.TO_ME_IS_CHILD && (rel.is_mortal || hasVisibleRelationMeta(rel))
    )
    const bloodOthers = rels.filter(rel =>
      rel.blood_relation
      && rel.blood_relation !== BloodRelationType.TO_ME_IS_PARENT
      && rel.blood_relation !== BloodRelationType.TO_ME_IS_CHILD
      && hasVisibleRelationMeta(rel)
    )
    const others = rels.filter(rel => !rel.blood_relation && hasVisibleRelationMeta(rel))

    return {
      parents: displayParents,
      children,
      bloodOthers,
      others,
    }
  })

  function formatGenderLabel(rawGender: string): string {
    if (rawGender === 'Male' || rawGender === 'male') return t('ui.create_avatar.gender_labels.male')
    if (rawGender === 'Female' || rawGender === 'female') return t('ui.create_avatar.gender_labels.female')
    return rawGender
  }

  function hasVisibleRelationMeta(rel: RelationInfo): boolean {
    return buildAvatarRelationMetaLines(rel).length > 0
  }

  function formatRelationSub(rel: RelationInfo): string {
    return [rel.sect?.trim(), formatCultivationText(rel.realm, t)].filter(Boolean).join(' · ')
  }

  function showDetail(item: EffectEntity | undefined) {
    if (item) {
      secondaryItem.value = item
    }
  }

  function openAdjustPanel(category: AvatarAdjustCategory) {
    adjustCategory.value = category
  }

  function closeAdjustPanel() {
    adjustCategory.value = null
  }

  function jumpToAvatar(id: string) {
    uiStore.select('avatar', id)
  }

  function jumpToSect(id: string) {
    uiStore.select('sect', id)
  }

  async function handleSetObjective() {
    if (!objectiveContent.value.trim()) return
    try {
      await avatarApi.setLongTermObjective(data().id, objectiveContent.value)
      showObjectiveModal.value = false
      objectiveContent.value = ''
      uiStore.refreshDetail()
    } catch (error) {
      logError('AvatarDetail.handleSetObjective', error)
      alertError(t('game.info_panel.avatar.modals.set_failed'))
    }
  }

  async function handleClearObjective() {
    if (!confirmClear(t('game.info_panel.avatar.modals.clear_confirm'))) return
    try {
      await avatarApi.clearLongTermObjective(data().id)
      uiStore.refreshDetail()
    } catch (error) {
      logError('AvatarDetail.handleClearObjective', error)
    }
  }

  return {
    secondaryItem,
    adjustCategory,
    showPortraitPanel,
    showObjectiveModal,
    objectiveContent,
    parsedCurrentEffects,
    portraitUrl,
    equipmentSlots,
    avatarHeaderSubtitle,
    avatarRealmText,
    formattedRanking,
    groupedRelations,
    formatGenderLabel,
    buildRelationMetaLines: buildAvatarRelationMetaLines,
    formatRelationSub,
    showDetail,
    openAdjustPanel,
    closeAdjustPanel,
    jumpToAvatar,
    jumpToSect,
    handleSetObjective,
    handleClearObjective,
  }
}
