<script setup lang="ts">
import { computed, watch } from 'vue'
import { NModal, NSpin, NTag } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useDynastyStore } from '@/stores/dynasty'
import { useUiStore } from '@/stores/ui'
import { formatCultivationText } from '@/utils/cultivationText'
import buildingIcon from '@/assets/icons/ui/lucide/building-2.svg'
import crownIcon from '@/assets/icons/ui/lucide/crown.svg'
import landmarkIcon from '@/assets/icons/ui/lucide/landmark.svg'
import scaleIcon from '@/assets/icons/ui/lucide/scale.svg'
import usersIcon from '@/assets/icons/ui/lucide/users.svg'

const props = defineProps<{
  show: boolean;
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
}>()

const { t } = useI18n()
const dynastyStore = useDynastyStore()
const uiStore = useUiStore()
const dynastyTheme = SYSTEM_PANEL_THEMES.dynasty
const panelStyleVars = {
  '--panel-accent': dynastyTheme.accent,
  '--panel-accent-strong': dynastyTheme.accentStrong,
  '--panel-accent-soft': dynastyTheme.accentSoft,
  '--panel-title': dynastyTheme.title,
  '--panel-empty': dynastyTheme.empty,
  '--panel-border': dynastyTheme.border,
  '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
  '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
}

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
      <div class="dynasty-overview" :style="panelStyleVars">
        <template v-if="hasOverview">
          <section class="hero-card">
            <div class="hero-header">
              <div class="hero-title-wrap">
                <span class="hero-icon" :style="{ '--icon-url': `url(${landmarkIcon})` }" aria-hidden="true"></span>
                <div>
                <div class="hero-title">{{ overview.title || overview.name }}</div>
                <div class="hero-subtitle">{{ t('game.dynasty.royal_house') }}：{{ overview.royal_house_name || overview.royal_surname }}</div>
                </div>
              </div>
              <n-tag size="small" :bordered="false" type="success">
                {{ t('game.dynasty.low_magic') }}
              </n-tag>
            </div>
            <div class="hero-desc">{{ overview.desc }}</div>
          </section>

        <section class="section">
            <div class="section-title">
              <span class="section-title-icon" :style="{ '--icon-url': `url(${buildingIcon})` }" aria-hidden="true"></span>
              {{ t('game.dynasty.summary.title') }}
            </div>
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
            <div class="section-title">
              <span class="section-title-icon" :style="{ '--icon-url': `url(${crownIcon})` }" aria-hidden="true"></span>
              {{ t('game.dynasty.emperor.title') }}
            </div>
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
            <div class="section-title">
              <span class="section-title-icon" :style="{ '--icon-url': `url(${scaleIcon})` }" aria-hidden="true"></span>
              {{ t('game.dynasty.effect') }}
            </div>
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
              <div class="section-title">
                <span class="section-title-icon" :style="{ '--icon-url': `url(${usersIcon})` }" aria-hidden="true"></span>
                {{ t('game.dynasty.officials.title') }}
              </div>
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
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(184, 121, 59, 0.34), rgba(69, 48, 30, 0.14)),
    rgba(255, 255, 255, 0.03);
}

.hero-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.hero-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.hero-icon {
  width: 28px;
  height: 28px;
  color: var(--panel-accent-strong);
  margin-top: 2px;
}

.hero-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--panel-text-primary);
}

.hero-subtitle {
  font-size: 13px;
  color: var(--panel-text-secondary);
  margin-top: 4px;
}

.hero-desc {
  color: var(--panel-text-secondary);
  line-height: 1.7;
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

.hero-icon,
.section-title-icon {
  display: inline-block;
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

.section-title-icon {
  width: 1em;
  height: 1em;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

.section-meta {
  font-size: 12px;
  color: var(--panel-text-secondary);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.info-card,
.effect-card {
  padding: 10px 12px;
  border: 1px solid var(--panel-border);
  border-radius: 6px;
  background: var(--panel-accent-soft);
}

.info-label {
  font-size: 12px;
  color: var(--panel-text-secondary);
  margin-bottom: 6px;
}

.info-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--panel-text-primary);
}

.effect-card {
  color: var(--panel-text-secondary);
  line-height: 1.7;
}

.effects-grid {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 4px 12px;
  align-items: baseline;
}

.effect-source {
  color: var(--panel-text-secondary);
  white-space: nowrap;
}

.effect-content {
  color: var(--panel-text-primary);
}

.emperor-tag {
  color: var(--panel-accent-strong);
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
  border: 1px solid var(--panel-border);
  border-radius: 6px;
  background: var(--panel-accent-soft);
  color: inherit;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.official-row:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--panel-accent);
}

.official-main {
  min-width: 0;
}

.official-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--panel-text-primary);
}

.official-rank {
  margin-top: 4px;
  font-size: 12px;
  color: var(--panel-accent-strong);
}

.official-side {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.official-meta {
  font-size: 12px;
  color: var(--panel-text-secondary);
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  color: var(--panel-empty);
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
