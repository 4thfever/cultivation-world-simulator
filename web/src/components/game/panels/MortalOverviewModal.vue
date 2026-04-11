<script setup lang="ts">
import { computed, watch } from 'vue'
import { NModal, NTable, NTag, NSpin } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useMortalStore } from '@/stores/mortal'
import {
  formatPopulationGrowthText,
  formatPopulationText,
} from '@/utils/populationFormat'
import buildingIcon from '@/assets/icons/ui/lucide/building-2.svg'
import usersIcon from '@/assets/icons/ui/lucide/users.svg'

const props = defineProps<{
  show: boolean;
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
}>()

const { locale, t } = useI18n()
const mortalStore = useMortalStore()
const mortalTheme = SYSTEM_PANEL_THEMES.mortal
const panelStyleVars = {
  '--panel-accent': mortalTheme.accent,
  '--panel-accent-strong': mortalTheme.accentStrong,
  '--panel-accent-soft': mortalTheme.accentSoft,
  '--panel-title': mortalTheme.title,
  '--panel-empty': mortalTheme.empty,
  '--panel-border': mortalTheme.border,
  '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
  '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
}

const summary = computed(() => mortalStore.overview.summary)
const cityRows = computed(() => mortalStore.overview.cities)
const trackedMortals = computed(() => mortalStore.overview.tracked_mortals)

function formatPopulation(value: number): string {
  return formatPopulationText(value, t, locale.value)
}

function formatNaturalGrowth(value: number): string {
  return formatPopulationGrowthText(value, t, locale.value)
}

function resolveBirthRegion(name: string): string {
  return name || t('game.mortal_system.tracked.unknown_region')
}

function handleShowChange(value: boolean) {
  emit('update:show', value)
}

watch(
  () => props.show,
  (show) => {
    if (show) {
      void mortalStore.refreshOverview()
    }
  },
)
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.mortal_system.title')"
    style="width: 980px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="mortalStore.isLoading">
      <div class="mortal-overview" :style="panelStyleVars">
        <section class="section">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${usersIcon})` }" aria-hidden="true"></span>
            {{ t('game.mortal_system.summary.title') }}
          </div>
          <div class="summary-grid">
            <div class="summary-card">
              <div class="summary-label">{{ t('game.mortal_system.summary.total_population') }}</div>
              <div class="summary-value">{{ formatPopulation(summary.total_population) }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">{{ t('game.mortal_system.summary.total_capacity') }}</div>
              <div class="summary-value">{{ formatPopulation(summary.total_population_capacity) }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">{{ t('game.mortal_system.summary.total_growth') }}</div>
              <div class="summary-value growth">{{ formatNaturalGrowth(summary.total_natural_growth) }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">{{ t('game.mortal_system.tracked.count') }}</div>
              <div class="summary-value">{{ summary.tracked_mortal_count }}</div>
            </div>
            <div class="summary-card">
              <div class="summary-label">{{ t('game.mortal_system.tracked.awakening_candidates') }}</div>
              <div class="summary-value">{{ summary.awakening_candidate_count }}</div>
            </div>
          </div>
        </section>

        <section class="section">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${buildingIcon})` }" aria-hidden="true"></span>
            {{ t('game.mortal_system.cities.title') }}
          </div>
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.mortal_system.cities.city') }}</th>
                <th>{{ t('game.mortal_system.cities.population') }}</th>
                <th>{{ t('game.mortal_system.cities.capacity') }}</th>
                <th>{{ t('game.mortal_system.cities.growth') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="city in cityRows" :key="city.id">
                <td>{{ city.name }}</td>
                <td>{{ formatPopulation(city.population) }}</td>
                <td>{{ formatPopulation(city.population_capacity) }}</td>
                <td>{{ formatNaturalGrowth(city.natural_growth) }}</td>
              </tr>
              <tr v-if="!cityRows.length">
                <td colspan="4" class="empty-cell">{{ t('game.mortal_system.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </section>

        <section class="section">
          <div class="section-title">{{ t('game.mortal_system.tracked.title') }}</div>
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.mortal_system.tracked.name') }}</th>
                <th>{{ t('game.mortal_system.tracked.gender') }}</th>
                <th>{{ t('game.mortal_system.tracked.age') }}</th>
                <th>{{ t('game.mortal_system.tracked.birth_region') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="mortal in trackedMortals" :key="mortal.id">
                <td>{{ mortal.name }}</td>
                <td>{{ mortal.gender }}</td>
                <td>{{ mortal.age }}</td>
                <td>{{ resolveBirthRegion(mortal.born_region_name) }}</td>
              </tr>
              <tr v-if="!trackedMortals.length">
                <td colspan="4" class="empty-cell">{{ t('game.mortal_system.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </section>
      </div>
    </n-spin>
  </n-modal>
</template>

<style scoped>
.mortal-overview {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: var(--panel-title);
  border-bottom: 1px solid var(--panel-border);
  padding-bottom: 6px;
}

.section-title-icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
  flex-shrink: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.summary-card {
  padding: 10px 12px;
  border: 1px solid var(--panel-border);
  border-radius: 6px;
  background: var(--panel-accent-soft);
}

.summary-label {
  font-size: 12px;
  color: var(--panel-text-secondary);
  margin-bottom: 6px;
}

.summary-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--panel-text-primary);
}

.summary-value.growth {
  color: var(--panel-accent-strong);
}

:deep(.n-table th) {
  color: var(--panel-text-secondary);
}

.empty-cell {
  text-align: center;
  color: var(--panel-empty);
}
</style>
