import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useUiStore } from '@/stores/ui'
import type { EffectEntity, RegionDetail } from '@/types/core'
import buildingIcon from '@/assets/icons/ui/lucide/building-2.svg'
import mapIcon from '@/assets/icons/ui/lucide/map.svg'
import mountainIcon from '@/assets/icons/ui/lucide/mountain.svg'

const ATTRIBUTE_KEYS = new Set(['GOLD', 'WOOD', 'WATER', 'FIRE', 'EARTH', 'ICE', 'WIND', 'DARK', 'THUNDER', 'EVIL'])

export function useRegionDetailPanel(data: () => RegionDetail) {
  const { t } = useI18n()
  const uiStore = useUiStore()
  const secondaryItem = ref<EffectEntity | null>(null)

  function getPopulationBarColor(ratio: number): string {
    if (ratio > 0.8) return '#52c41a'
    if (ratio > 0.3) return '#1890ff'
    return '#ff4d4f'
  }

  function formatEssenceType(rawType: string | undefined): string {
    if (!rawType) return ''
    return rawType
      .split(',')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const normalized = part.toUpperCase()
        return ATTRIBUTE_KEYS.has(normalized) ? t(`attributes.${normalized}`) : part
      })
      .join('、')
  }

  function getRegionTypeExplanation(): string {
    const region = data()
    if (region.type === 'city') return t('game.info_panel.region.type_explanations.city')
    if (region.type === 'cultivate') {
      return region.sub_type === 'ruin'
        ? t('game.info_panel.region.type_explanations.ruin')
        : t('game.info_panel.region.type_explanations.cave')
    }
    if (region.type === 'sect') return t('game.info_panel.region.type_explanations.sect')
    return t('game.info_panel.region.type_explanations.normal')
  }

  function getRegionTypeIcon(): string {
    const region = data()
    if (region.type === 'city') return buildingIcon
    if (region.type === 'cultivate') return mountainIcon
    return mapIcon
  }

  function showDetail(item: EffectEntity | undefined) {
    if (item) {
      secondaryItem.value = item
    }
  }

  function closeSecondaryDetail() {
    secondaryItem.value = null
  }

  function jumpToSect(id: number) {
    void uiStore.select('sect', id.toString())
  }

  function jumpToAvatar(id: string) {
    void uiStore.select('avatar', id)
  }

  return {
    secondaryItem,
    getPopulationBarColor,
    formatEssenceType,
    getRegionTypeExplanation,
    getRegionTypeIcon,
    showDetail,
    closeSecondaryDetail,
    jumpToSect,
    jumpToAvatar,
  }
}
