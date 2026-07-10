<script setup lang="ts">
import { computed, watch } from 'vue'
import { NModal, NSpin } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { useWorldSecretStore } from '@/stores/worldSecret'
import scrollTextIcon from '@/assets/icons/ui/lucide/scroll-text.svg'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const store = useWorldSecretStore()

const overview = computed(() => store.overview)
const activeSecret = computed(() => overview.value?.active_secret)

watch(
  () => props.show,
  (visible) => {
    if (visible) void store.refreshOverview()
  },
  { immediate: true },
)

function handleShowChange(value: boolean) {
  emit('update:show', value)
}

function decisionLabel(decision?: string | null) {
  if (decision === 'share_all') return t('game.world_secret.decision_share')
  if (decision === 'keep_secret') return t('game.world_secret.decision_keep')
  return t('game.world_secret.decision_none')
}
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.world_secret.title')"
    style="width: 900px; max-height: 82vh; overflow-y: auto;"
  >
    <div class="world-secret-panel">
      <div class="panel-caption">
        <span class="caption-icon" :style="{ '--icon-url': `url(${scrollTextIcon})` }" aria-hidden="true"></span>
        {{ t('game.world_secret.caption') }}
      </div>

      <n-spin :show="store.loading">
        <div v-if="activeSecret" class="secret-body">
          <section class="secret-summary">
            <div class="summary-title">{{ activeSecret.title }}</div>
            <div v-if="activeSecret.id === 'none'" class="summary-secret muted">
              {{ t('game.world_secret.none_desc') }}
            </div>
            <div v-else class="summary-secret">{{ activeSecret.secret }}</div>
            <div class="summary-meta">
              <span>{{ t('game.world_secret.fragment_count', { count: activeSecret.fragment_count }) }}</span>
              <span v-if="overview?.public_revealed">
                {{ t('game.world_secret.public_revealed') }}
                <template v-if="overview.public_revealed_by">
                  · {{ overview.public_revealed_by.name }}
                </template>
              </span>
              <span v-else>{{ t('game.world_secret.not_public') }}</span>
            </div>
          </section>

          <section v-if="overview?.avatars?.length" class="knowledge-section">
            <h4>{{ t('game.world_secret.known_avatars') }}</h4>
            <div class="avatar-grid">
              <div v-for="avatar in overview.avatars" :key="avatar.id" class="avatar-row">
                <span class="avatar-name">
                  {{ avatar.name }}<span v-if="avatar.is_dead" class="dead-tag">{{ t('game.deceased.title_short') }}</span>
                </span>
                <span class="avatar-progress">
                  {{ avatar.known_fragment_count }} / {{ avatar.fragment_count }}
                </span>
                <span class="avatar-full" :class="{ active: avatar.knows_full_secret }">
                  {{ avatar.knows_full_secret ? t('game.world_secret.knows_full') : t('game.world_secret.fragments_only') }}
                </span>
                <span class="avatar-decision">{{ decisionLabel(avatar.decision) }}</span>
              </div>
            </div>
          </section>

          <section v-if="overview?.fragments?.length" class="knowledge-section">
            <h4>{{ t('game.world_secret.fragments') }}</h4>
            <div class="fragment-list">
              <article v-for="fragment in overview.fragments" :key="fragment.id" class="fragment-item">
                <div class="fragment-head">
                  <span>{{ fragment.order }}. {{ fragment.angle }}</span>
                  <span class="known-count">
                    {{ t('game.world_secret.known_by_count', { count: fragment.known_by.length }) }}
                  </span>
                </div>
                <p>{{ fragment.text }}</p>
                <div class="known-by">
                  <span v-if="fragment.known_by.length === 0" class="muted">
                    {{ t('game.world_secret.no_one_knows') }}
                  </span>
                  <span v-for="avatar in fragment.known_by" :key="avatar.id" class="known-chip">
                    {{ avatar.name }}<span v-if="avatar.is_dead">{{ t('game.deceased.title_short') }}</span>
                  </span>
                </div>
              </article>
            </div>
          </section>
        </div>

        <div v-else class="empty">
          {{ store.loading ? t('common.loading') : t('game.world_secret.empty') }}
        </div>
      </n-spin>
    </div>
  </n-modal>
</template>

<style scoped>
.world-secret-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  color: #efece5;
}

.panel-caption {
  display: flex;
  align-items: center;
  gap: 7px;
  padding-bottom: 10px;
  border-bottom: 1px solid #332f37;
  color: #d5b5e6;
  font-size: 13px;
}

.caption-icon {
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

.secret-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.secret-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.summary-title {
  color: #f0c9ff;
  font-size: 18px;
  font-weight: 700;
}

.summary-secret {
  color: #e6dfd0;
  font-size: 14px;
  line-height: 1.8;
}

.summary-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: #ad9fb5;
  font-size: 12px;
}

.knowledge-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.knowledge-section h4 {
  margin: 0;
  color: #dec0ed;
  font-size: 14px;
}

.avatar-grid {
  display: grid;
  gap: 6px;
}

.avatar-row {
  display: grid;
  grid-template-columns: minmax(120px, 1fr) 70px 90px 90px;
  gap: 10px;
  align-items: center;
  padding: 8px 10px;
  border: 1px solid rgba(213, 181, 230, 0.14);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.035);
  font-size: 13px;
}

.avatar-name {
  color: #f1e7f6;
  min-width: 0;
}

.dead-tag {
  margin-left: 4px;
  color: #9e909f;
  font-size: 12px;
}

.avatar-progress,
.avatar-decision {
  color: #b9aabd;
}

.avatar-full {
  color: #9f929f;
}

.avatar-full.active {
  color: #daba74;
}

.fragment-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.fragment-item {
  padding: 10px 0;
  border-bottom: 1px solid #312c35;
}

.fragment-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #e4c5f0;
  font-size: 13px;
  font-weight: 600;
}

.known-count {
  color: #ad9fb5;
  font-weight: 400;
  white-space: nowrap;
}

.fragment-item p {
  margin: 7px 0;
  color: #dad0dc;
  font-size: 13px;
  line-height: 1.75;
}

.known-by {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.known-chip {
  padding: 2px 7px;
  border: 1px solid rgba(213, 181, 230, 0.2);
  border-radius: 6px;
  color: #e8daf0;
  background: rgba(213, 181, 230, 0.08);
  font-size: 12px;
}

.muted,
.empty {
  color: #9f929f;
}

.empty {
  padding: 14px 0;
  font-size: 13px;
}

@media (max-width: 700px) {
  .avatar-row {
    grid-template-columns: 1fr 64px;
  }

  .avatar-full,
  .avatar-decision {
    grid-column: span 1;
  }

  .fragment-head {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
