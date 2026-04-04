<script setup lang="ts">
import { computed, watch } from 'vue'
import { NModal, NSpin, NTag } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useDynastyStore } from '@/stores/dynasty'
import { useUiStore } from '@/stores/ui'
import { formatCultivationText } from '@/utils/cultivationText'

const props = defineProps<{
  show: boolean;
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
}>()

const { t } = useI18n()
const dynastyStore = useDynastyStore()
const uiStore = useUiStore()

const overview = computed(() => dynastyStore.overview)
const officials = computed(() => dynastyStore.officials)
const summary = computed(() => dynastyStore.summary)
const hasOverview = computed(() => Boolean(overview.value.name))
const emperor = computed(() => overview.value.current_emperor)
const effectLines = computed(() => {
  const text = overview.value.effect_desc || ''
  if (!text) return []
  return text.split(/[;\n；]/).map((line) => line.trim()).filter(Boolean)
})

function jumpToAvatar(id: string) {
  void uiStore.select('avatar', id)
}

function handleShowChange(value: boolean) {
  emit('update:show', value)
}

watch(
  () => props.show,
  (show) => {
    if (show) {
      void dynastyStore.refreshDetail()
    }
  },
)
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.dynasty.title')"
    style="width: 760px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="dynastyStore.isLoading">
      <div class="dynasty-overview">
        <template v-if="hasOverview">
          <section class="hero-card">
            <div class="hero-header">
              <div>
                <div class="hero-title">{{ overview.title || overview.name }}</div>
                <div class="hero-subtitle">{{ t('game.dynasty.royal_house') }}：{{ overview.royal_house_name || overview.royal_surname }}</div>
              </div>
              <n-tag size="small" :bordered="false" type="success">
                {{ t('game.dynasty.low_magic') }}
              </n-tag>
            </div>
            <div class="hero-desc">{{ overview.desc }}</div>
          </section>

          <section class="section">
            <div class="section-title">{{ t('game.dynasty.summary.title') }}</div>
            <div class="info-grid">
              <div class="info-card">
                <div class="info-label">{{ t('game.dynasty.name') }}</div>
                <div class="info-value">{{ overview.name }}</div>
              </div>
              <div class="info-card">
                <div class="info-label">{{ t('game.dynasty.royal_house') }}</div>
                <div class="info-value">{{ overview.royal_house_name || overview.royal_surname }}</div>
              </div>
              <div class="info-card">
                <div class="info-label">{{ t('game.dynasty.style_tag') }}</div>
                <div class="info-value">{{ overview.style_tag || t('common.none') }}</div>
              </div>
              <div class="info-card">
                <div class="info-label">{{ t('game.dynasty.official_preference') }}</div>
                <div class="info-value">{{ overview.official_preference_label || t('common.none') }}</div>
              </div>
            </div>
          </section>

          <section class="section">
            <div class="section-title">{{ t('game.dynasty.emperor.title') }}</div>
            <div v-if="emperor" class="info-grid">
              <div class="info-card">
                <div class="info-label">{{ t('game.dynasty.emperor.name') }}</div>
                <div class="info-value">{{ emperor.name }}</div>
              </div>
              <div class="info-card">
                <div class="info-label">{{ t('game.dynasty.emperor.age') }}</div>
                <div class="info-value">{{ emperor.age }}</div>
              </div>
              <div class="info-card">
                <div class="info-label">{{ t('game.dynasty.emperor.lifespan') }}</div>
                <div class="info-value">{{ emperor.max_age }}</div>
              </div>
              <div class="info-card">
                <div class="info-label">{{ t('game.dynasty.emperor.identity') }}</div>
                <div class="info-value emperor-tag">{{ t('game.dynasty.emperor.mortal') }}</div>
              </div>
            </div>
            <div v-else class="empty-state section-empty">
              {{ t('game.dynasty.emperor.empty') }}
            </div>
          </section>

          <section class="section">
            <div class="section-title">{{ t('game.dynasty.effect') }}</div>
            <div v-if="effectLines.length" class="effect-card">
              <div class="effects-grid">
                <template v-for="(line, idx) in effectLines" :key="idx">
                  <div class="effect-source">{{ t('game.dynasty.effect_source') }}</div>
                  <div class="effect-content">{{ line }}</div>
                </template>
              </div>
            </div>
            <div v-else class="effect-card">
              {{ t('game.dynasty.effect_empty') }}
            </div>
          </section>

          <section class="section">
            <div class="section-header">
              <div class="section-title">{{ t('game.dynasty.officials.title') }}</div>
              <div class="section-meta">{{ t('game.dynasty.officials.count', { count: summary.officialCount }) }}</div>
            </div>
            <div v-if="officials.length" class="official-list">
              <button
                v-for="official in officials"
                :key="official.id"
                class="official-row"
                type="button"
                @click="jumpToAvatar(official.id)"
              >
                <div class="official-main">
                  <div class="official-name">{{ official.name }}</div>
                  <div class="official-rank">{{ official.officialRankName }}</div>
                </div>
                <div class="official-side">
                  <div class="official-meta">
                    {{ t('game.dynasty.officials.realm') }}：{{ formatCultivationText(official.realm, t) || t('common.none') }}
                  </div>
                  <div class="official-meta">
                    {{ t('game.dynasty.officials.court_reputation') }}：{{ official.courtReputation }}
                  </div>
                  <div class="official-meta">
                    {{ t('game.dynasty.officials.sect') }}：{{ official.sectName || t('game.dynasty.officials.rogue') }}
                  </div>
                </div>
              </button>
            </div>
            <div v-else class="empty-state section-empty">
              {{ t('game.dynasty.officials.empty') }}
            </div>
          </section>
        </template>

        <div v-else class="empty-state">
          {{ t('game.dynasty.empty') }}
        </div>
      </div>
    </n-spin>
  </n-modal>
</template>

<style scoped>
.dynasty-overview {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border: 1px solid #2f2f2f;
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(124, 45, 18, 0.35), rgba(107, 33, 168, 0.08)),
    rgba(255, 255, 255, 0.03);
}

.hero-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.hero-title {
  font-size: 24px;
  font-weight: 700;
  color: #f5f5f5;
}

.hero-subtitle {
  font-size: 13px;
  color: #d9d9d9;
  margin-top: 4px;
}

.hero-desc {
  color: #cfcfcf;
  line-height: 1.7;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-title {
  font-size: 13px;
  font-weight: 700;
  color: #d9d9d9;
  border-bottom: 1px solid #333;
  padding-bottom: 6px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.section-meta {
  font-size: 12px;
  color: #8c8c8c;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.info-card,
.effect-card {
  padding: 10px 12px;
  border: 1px solid #2f2f2f;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
}

.info-label {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 6px;
}

.info-value {
  font-size: 18px;
  font-weight: 700;
  color: #f5f5f5;
}

.effect-card {
  color: #d9d9d9;
  line-height: 1.7;
}

.effects-grid {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 4px 12px;
  align-items: baseline;
}

.effect-source {
  color: #8c8c8c;
  white-space: nowrap;
}

.effect-content {
  color: #d9d9d9;
}

.emperor-tag {
  color: #ffd591;
}

.official-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.official-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  width: 100%;
  padding: 12px;
  border: 1px solid #2f2f2f;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.official-row:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: #4a4a4a;
}

.official-main {
  min-width: 0;
}

.official-name {
  font-size: 16px;
  font-weight: 700;
  color: #f5f5f5;
}

.official-rank {
  margin-top: 4px;
  font-size: 12px;
  color: #ffd591;
}

.official-side {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.official-meta {
  font-size: 12px;
  color: #bfbfbf;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  color: #888;
  padding: 20px 0;
}

.section-empty {
  padding: 10px 0;
}

@media (max-width: 640px) {
  .official-row {
    grid-template-columns: 1fr;
  }

  .official-side {
    align-items: flex-start;
  }
}
</style>
