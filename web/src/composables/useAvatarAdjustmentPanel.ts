import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { avatarApi } from '@/api'
import type { AvatarAdjustCatalogDTO, AvatarAdjustOptionDTO, CustomContentDraftDTO } from '@/types/api'
import type { EffectEntity } from '@/types/core'
import { getEntityGradeTone } from '@/utils/theme'
import { logError, toErrorMessage } from '@/utils/appError'

export type AdjustCategory = 'technique' | 'weapon' | 'auxiliary' | 'personas' | 'goldfinger'

export interface AvatarAdjustmentPanelProps {
  avatarId: string
  category: AdjustCategory | null
  currentItem?: EffectEntity | null
  currentPersonas?: EffectEntity[]
}

interface AvatarAdjustmentPanelCallbacks {
  onClose: () => void
  onUpdated: () => void
}

function isCustomContentCategory(
  category: AdjustCategory | null,
): category is 'technique' | 'weapon' | 'auxiliary' | 'goldfinger' {
  return category === 'technique'
    || category === 'weapon'
    || category === 'auxiliary'
    || category === 'goldfinger'
}

const categoryLabels: Record<AdjustCategory, string> = {
  technique: 'game.info_panel.avatar.adjust.categories.technique',
  weapon: 'game.info_panel.avatar.adjust.categories.weapon',
  auxiliary: 'game.info_panel.avatar.adjust.categories.auxiliary',
  personas: 'game.info_panel.avatar.adjust.categories.personas',
  goldfinger: 'game.info_panel.avatar.adjust.categories.goldfinger',
}

export function useAvatarAdjustmentPanel(
  props: AvatarAdjustmentPanelProps,
  callbacks: AvatarAdjustmentPanelCallbacks,
) {
  const { t } = useI18n()
  const message = useMessage()

  const catalog = ref<AvatarAdjustCatalogDTO | null>(null)
  const isLoading = ref(false)
  const submitLoading = ref(false)
  const errorText = ref('')
  const searchText = ref('')
  const selectedPersonaIds = ref<number[]>([])
  const customRealm = ref('CORE_FORMATION')
  const customPrompt = ref('')
  const customDraft = ref<CustomContentDraftDTO | null>(null)
  const draftLoading = ref(false)
  const saveDraftLoading = ref(false)

  const singleSlotCurrentItem = computed(() => props.currentItem ?? null)
  const currentPersonaSummary = computed(() => props.currentPersonas?.length ? props.currentPersonas : [])

  const panelTitle = computed(() => {
    if (!props.category) return ''
    return t('game.info_panel.avatar.adjust.title', {
      category: t(categoryLabels[props.category]),
    })
  })

  const availableOptions = computed<AvatarAdjustOptionDTO[]>(() => {
    if (!catalog.value || !props.category) return []
    switch (props.category) {
      case 'technique':
        return catalog.value.techniques
      case 'weapon':
        return catalog.value.weapons
      case 'auxiliary':
        return catalog.value.auxiliaries
      case 'personas':
        return catalog.value.personas
      case 'goldfinger':
        return catalog.value.goldfingers
    }
  })

  const normalizedSearch = computed(() => searchText.value.trim().toLowerCase())
  const supportsCustomGeneration = computed(() => isCustomContentCategory(props.category))
  const needsRealmForCustomGeneration = computed(() => (
    props.category === 'weapon' || props.category === 'auxiliary'
  ))

  const realmOptions = computed(() => [
    { value: 'QI_REFINEMENT', label: t('realms.QI_REFINEMENT') },
    { value: 'FOUNDATION_ESTABLISHMENT', label: t('realms.FOUNDATION_ESTABLISHMENT') },
    { value: 'CORE_FORMATION', label: t('realms.CORE_FORMATION') },
    { value: 'NASCENT_SOUL', label: t('realms.NASCENT_SOUL') },
  ])

  const draftPreviewItem = computed<EffectEntity | null>(() => {
    if (!customDraft.value) return null
    return {
      ...customDraft.value,
      name: customDraft.value.name || t('game.info_panel.avatar.adjust.custom.unnamed'),
      grade: customDraft.value.grade ? t(`technique_grades.${customDraft.value.grade}`) : customDraft.value.grade,
      attribute: customDraft.value.attribute ? t(`attributes.${customDraft.value.attribute}`) : customDraft.value.attribute,
      realm: customDraft.value.realm ? t(`realms.${customDraft.value.realm}`) : customDraft.value.realm,
    }
  })

  const filteredOptions = computed(() => {
    const query = normalizedSearch.value
    const rawOptions = availableOptions.value
    const result = !query
      ? rawOptions
      : rawOptions.filter(option => {
          const haystack = `${option.name} ${option.desc || ''} ${option.effect_desc || ''} ${option.grade || ''} ${option.rarity || ''} ${option.attribute || ''}`
          return haystack.toLowerCase().includes(query)
        })

    if (props.category === 'personas') return result

    return [
      {
        id: '__none__',
        name: t('common.none'),
        desc: '',
      } as AvatarAdjustOptionDTO,
      ...result,
    ]
  })

  function getOptionGradeClass(option: Pick<EffectEntity, 'grade' | 'rarity'>): string {
    return `option-meta-${getEntityGradeTone(option.grade || option.rarity)}`
  }

  function syncSelectedPersonas() {
    selectedPersonaIds.value = (props.currentPersonas || [])
      .map(persona => Number(persona.id))
      .filter(id => Number.isFinite(id))
  }

  async function ensureCatalogLoaded() {
    if (catalog.value || isLoading.value) return
    isLoading.value = true
    errorText.value = ''
    try {
      catalog.value = await avatarApi.fetchAvatarAdjustOptions()
    } catch (error) {
      logError('AvatarAdjustPanel.fetchAvatarAdjustOptions', error)
      errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.load_failed'))
    } finally {
      isLoading.value = false
    }
  }

  async function reloadCatalog() {
    catalog.value = null
    await ensureCatalogLoaded()
  }

  function isSelectedPersona(option: AvatarAdjustOptionDTO) {
    return selectedPersonaIds.value.includes(Number(option.id))
  }

  function togglePersona(option: AvatarAdjustOptionDTO) {
    const id = Number(option.id)
    if (!Number.isFinite(id)) return
    if (isSelectedPersona(option)) {
      selectedPersonaIds.value = selectedPersonaIds.value.filter(item => item !== id)
      return
    }
    selectedPersonaIds.value = [...selectedPersonaIds.value, id]
  }

  async function handleSingleSelect(option: AvatarAdjustOptionDTO) {
    if (!props.category || props.category === 'personas' || submitLoading.value || saveDraftLoading.value) return

    submitLoading.value = true
    errorText.value = ''
    try {
      await avatarApi.updateAvatarAdjustment({
        avatar_id: props.avatarId,
        category: props.category,
        target_id: option.id === '__none__' ? null : Number(option.id),
      })
      message.success(t('game.info_panel.avatar.adjust.apply_success'))
      callbacks.onUpdated()
      callbacks.onClose()
    } catch (error) {
      logError('AvatarAdjustPanel.updateSingle', error)
      errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.apply_failed'))
    } finally {
      submitLoading.value = false
    }
  }

  async function applyPersonas() {
    if (submitLoading.value) return
    submitLoading.value = true
    errorText.value = ''
    try {
      await avatarApi.updateAvatarAdjustment({
        avatar_id: props.avatarId,
        category: 'personas',
        persona_ids: selectedPersonaIds.value,
      })
      message.success(t('game.info_panel.avatar.adjust.apply_success'))
      callbacks.onUpdated()
      callbacks.onClose()
    } catch (error) {
      logError('AvatarAdjustPanel.applyPersonas', error)
      errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.apply_failed'))
    } finally {
      submitLoading.value = false
    }
  }

  async function generateCustomDraft() {
    if (!isCustomContentCategory(props.category) || draftLoading.value) return
    if (!customPrompt.value.trim()) {
      errorText.value = t('game.info_panel.avatar.adjust.custom.prompt_required')
      return
    }

    draftLoading.value = true
    errorText.value = ''
    customDraft.value = null
    try {
      const response = await avatarApi.generateCustomContent({
        category: props.category,
        realm: needsRealmForCustomGeneration.value ? customRealm.value : undefined,
        user_prompt: customPrompt.value.trim(),
      })
      customDraft.value = response.draft
    } catch (error) {
      logError('AvatarAdjustPanel.generateCustomDraft', error)
      errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.custom.generate_failed'))
    } finally {
      draftLoading.value = false
    }
  }

  async function saveCustomDraft() {
    if (!isCustomContentCategory(props.category) || !customDraft.value || saveDraftLoading.value) return

    saveDraftLoading.value = true
    errorText.value = ''
    try {
      const createResponse = await avatarApi.createCustomContent({
        category: props.category,
        draft: customDraft.value,
      })
      await reloadCatalog()
      await avatarApi.updateAvatarAdjustment({
        avatar_id: props.avatarId,
        category: props.category,
        target_id: Number(createResponse.item.id),
      })
      message.success(t('game.info_panel.avatar.adjust.custom.create_success'))
      callbacks.onUpdated()
      callbacks.onClose()
    } catch (error) {
      logError('AvatarAdjustPanel.saveCustomDraft', error)
      errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.custom.create_failed'))
    } finally {
      saveDraftLoading.value = false
    }
  }

  watch(
    () => props.currentPersonas,
    () => {
      if (props.category === 'personas') {
        syncSelectedPersonas()
      }
    },
    { immediate: true, deep: true },
  )

  watch(
    () => props.category,
    async category => {
      searchText.value = ''
      errorText.value = ''
      customPrompt.value = ''
      customDraft.value = null
      if (category === 'personas') {
        syncSelectedPersonas()
      }
      if (category) {
        await ensureCatalogLoaded()
      }
    },
    { immediate: true },
  )

  return {
    isLoading,
    submitLoading,
    errorText,
    searchText,
    customRealm,
    customPrompt,
    customDraft,
    draftLoading,
    saveDraftLoading,
    singleSlotCurrentItem,
    currentPersonaSummary,
    panelTitle,
    supportsCustomGeneration,
    needsRealmForCustomGeneration,
    realmOptions,
    draftPreviewItem,
    filteredOptions,
    getOptionGradeClass,
    isSelectedPersona,
    togglePersona,
    handleSingleSelect,
    applyPersonas,
    generateCustomDraft,
    saveCustomDraft,
  }
}
