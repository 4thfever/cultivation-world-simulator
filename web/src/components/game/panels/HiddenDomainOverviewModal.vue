<script setup lang="ts">
import { computed } from 'vue'
import { NModal, NEmpty, NTag } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors'
import { useWorldStore } from '@/stores/world'
import { formatRealmLabel } from '@/utils/cultivationText'
import shieldIcon from '@/assets/icons/ui/lucide/shield.svg'
import sparklesIcon from '@/assets/icons/ui/lucide/sparkles.svg'
import clockIcon from '@/assets/icons/ui/lucide/clock-3.svg'
import triangleAlertIcon from '@/assets/icons/ui/lucide/triangle-alert.svg'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const worldStore = useWorldStore()
const hiddenDomainTheme = SYSTEM_PANEL_THEMES.hiddenDomain
const panelStyleVars = {
  '--panel-accent': hiddenDomainTheme.accent,
  '--panel-accent-strong': hiddenDomainTheme.accentStrong,
  '--panel-accent-soft': hiddenDomainTheme.accentSoft,
  '--panel-title': hiddenDomainTheme.title,
  '--panel-empty': hiddenDomainTheme.empty,
  '--panel-border': hiddenDomainTheme.border,
  '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
  '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
}

const domainItems = computed(() => worldStore.activeDomains)

function handleShowChange(value: boolean) {
  emit('update:show', value)
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(0)}%`
}
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.status_bar.hidden_domain.title')"
    style="width: 860px; max-height: 80vh; overflow-y: auto;"
  >
    <div class="hidden-domain-overview" :style="panelStyleVars">
      <section class="hero-card">
        <div class="hero-title-wrap">
          <span class="hero-icon" :style="{ '--icon-url': `url(${shieldIcon})` }" aria-hidden="true"></span>
          <div>
            <div class="hero-title">{{ t('game.status_bar.hidden_domain.title') }}</div>
            <div class="hero-subtitle">{{ t('game.world_info.entries.WORLD_INFO_SECRET_REALM_DESC') }}</div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="section-header">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${sparklesIcon})` }" aria-hidden="true"></span>
            {{ t('game.status_bar.hidden_domain.title') }}
          </div>
          <div class="section-meta">{{ domainItems.length }}</div>
        </div>

        <div v-if="domainItems.length" class="domain-list">
          <article
            v-for="item in domainItems"
            :key="item.id"
            class="domain-card"
          >
            <div class="domain-card-header">
              <div>
                <div class="domain-name">{{ item.name }}</div>
                <div class="domain-desc">{{ item.desc }}</div>
              </div>
              <n-tag size="small" :bordered="false" class="realm-tag">
                {{ t('game.status_bar.hidden_domain.required_realm') }}：{{ formatRealmLabel(item.required_realm, t) }}
              </n-tag>
            </div>

            <div class="stats-grid">
              <div class="stat-card stat-card-danger">
                <div class="stat-title">
                  <span class="stat-icon" :style="{ '--icon-url': `url(${triangleAlertIcon})` }" aria-hidden="true"></span>
                  {{ t('game.status_bar.hidden_domain.danger') }}
                </div>
                <div class="stat-value">{{ formatPercent(item.danger_prob) }}</div>
              </div>
              <div class="stat-card stat-card-drop">
                <div class="stat-title">
                  <span class="stat-icon" :style="{ '--icon-url': `url(${sparklesIcon})` }" aria-hidden="true"></span>
                  {{ t('game.status_bar.hidden_domain.drop') }}
                </div>
                <div class="stat-value">{{ formatPercent(item.drop_prob) }}</div>
              </div>
              <div class="stat-card stat-card-cooldown">
                <div class="stat-title">
                  <span class="stat-icon" :style="{ '--icon-url': `url(${clockIcon})` }" aria-hidden="true"></span>
                  {{ t('game.status_bar.hidden_domain.cooldown') }}
                </div>
                <div class="stat-value">{{ item.cd_years }}{{ t('common.year') }}</div>
              </div>
              <div class="stat-card stat-card-chance">
                <div class="stat-title">
                  <span class="stat-icon" :style="{ '--icon-url': `url(${shieldIcon})` }" aria-hidden="true"></span>
                  {{ t('game.status_bar.hidden_domain.open_chance') }}
                </div>
                <div class="stat-value">{{ formatPercent(item.open_prob) }}</div>
              </div>
            </div>
          </article>
        </div>

        <n-empty
          v-else
          :description="t('game.status_bar.hidden_domain.empty')"
          class="empty-state"
        />
      </section>
    </div>
  </n-modal>
</template>

<style scoped>
.hidden-domain-overview {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-card {
  padding: 14px;
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgba(183, 138, 82, 0.34), rgba(74, 55, 38, 0.12)),
    rgba(255, 255, 255, 0.03);
}

.hero-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.hero-icon,
.section-title-icon,
.stat-icon {
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
  margin-top: 4px;
  line-height: 1.7;
  color: var(--panel-text-secondary);
  font-size: 14px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
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
  flex: 1;
}

.section-title-icon,
.stat-icon {
  width: 1em;
  height: 1em;
}

.section-meta {
  font-size: 12px;
  color: var(--panel-text-secondary);
}

.domain-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.domain-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  border: 1px solid var(--panel-border);
  border-radius: 8px;
  background: var(--panel-accent-soft);
}

.domain-card-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.domain-name {
  font-size: 19px;
  font-weight: 700;
  color: var(--panel-text-primary);
}

.domain-desc {
  margin-top: 6px;
  font-size: 14px;
  line-height: 1.75;
  color: var(--panel-text-secondary);
}

.realm-tag {
  flex-shrink: 0;
  color: var(--panel-accent-strong);
  background: rgba(255, 255, 255, 0.08);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.stat-card {
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.04);
}

.stat-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--panel-text-secondary);
}

.stat-value {
  margin-top: 8px;
  font-size: 20px;
  font-weight: 700;
  color: var(--panel-text-primary);
}

.stat-card-danger .stat-value {
  color: #e39a89;
}

.stat-card-drop .stat-value {
  color: #e4c472;
}

.stat-card-cooldown .stat-value {
  color: #9fc5de;
}

.stat-card-chance .stat-value {
  color: #9fd4a1;
}

.empty-state {
  padding: 20px 0;
}

@media (max-width: 720px) {
  .domain-card-header {
    flex-direction: column;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
