<script setup lang="ts">
import type { ComposerTranslation } from 'vue-i18n'
import type { AvatarDetail, EffectEntity } from '@/types/core'
import StatItem from '../components/StatItem.vue'
import { formatHp } from '@/utils/formatters/number'
import { formatCultivationText } from '@/utils/cultivationText'

defineProps<{
  data: AvatarDetail
  formattedRanking: string | null
  formatGenderLabel: (gender: string) => string
  t: ComposerTranslation
}>()

const emit = defineEmits<{
  (e: 'show-detail', item: EffectEntity | undefined): void
  (e: 'jump-sect', id: string): void
}>()
</script>

<template>
  <div class="stats-grid">
    <StatItem
      :label="t('game.info_panel.avatar.stats.realm')"
      :value="data.cultivation?.display_full_name || formatCultivationText(data.realm, t)"
      :sub-value="data.cultivation && data.cultivation.canonical_full_name !== data.cultivation.display_full_name ? data.cultivation.canonical_full_name : undefined"
    />
    <StatItem :label="t('game.info_panel.avatar.stats.age')" :value="`${data.age} / ${data.lifespan}`" />
    <StatItem
      v-if="data.cultivation_start_age !== undefined"
      :label="t('game.info_panel.avatar.stats.awakened_age')"
      :value="`${data.cultivation_start_age}`"
    />
    <StatItem :label="t('game.info_panel.avatar.stats.origin')" :value="data.origin" />

    <StatItem :label="t('game.info_panel.avatar.stats.hp')" :value="formatHp(data.hp.cur, data.hp.max)" />
    <StatItem :label="t('game.info_panel.avatar.stats.gender')" :value="formatGenderLabel(data.gender)" />
    <StatItem
      :label="t('game.info_panel.avatar.stats.race')"
      :value="data.race?.name || t('game.info_panel.avatar.stats.unknown_race')"
      :on-click="() => emit('show-detail', data.race)"
    />

    <StatItem
      :label="t('game.info_panel.avatar.stats.alignment')"
      :value="data.alignment"
      :on-click="() => emit('show-detail', data.alignment_detail)"
    />
    <StatItem
      :label="t('game.info_panel.avatar.stats.sect')"
      :value="data.sect?.name || t('game.info_panel.avatar.stats.rogue')"
      :sub-value="data.sect?.rank"
      :on-click="data.sect ? () => emit('jump-sect', data.sect!.id) : (data.orthodoxy ? () => emit('show-detail', data.orthodoxy) : undefined)"
    />
    <StatItem
      :label="t('game.info_panel.avatar.stats.official_rank')"
      :value="data.official_rank || t('common.none')"
      :sub-value="data.court_reputation !== undefined ? `${t('game.info_panel.avatar.stats.court_reputation')} ${data.court_reputation}` : undefined"
    />

    <StatItem
      :label="t('game.info_panel.avatar.stats.root')"
      :value="data.root"
      :on-click="() => emit('show-detail', data.root_detail)"
    />
    <StatItem :label="t('game.info_panel.avatar.stats.luck')" :value="data.luck" />
    <StatItem :label="t('game.info_panel.avatar.stats.magic_stone')" :value="data.magic_stone" />
    <StatItem :label="t('game.info_panel.avatar.stats.sect_contribution')" :value="data.sect_contribution ?? 0" />
    <StatItem :label="t('game.info_panel.avatar.stats.appearance')" :value="data.appearance" />
    <StatItem :label="t('game.info_panel.avatar.stats.battle_strength')" :value="data.base_battle_strength" />
    <StatItem
      v-if="formattedRanking"
      :label="t('game.info_panel.avatar.stats.ranking')"
      :value="formattedRanking"
    />
    <StatItem
      :label="t('game.info_panel.avatar.stats.emotion')"
      :value="data.emotion.emoji"
      :sub-value="data.emotion.name"
    />
  </div>
</template>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
  gap: 8px;
}
</style>
