<script setup lang="ts">
import { NModal } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useWorldInfo } from '@/composables/useWorldInfo'
import bookOpenIcon from '@/assets/icons/ui/lucide/book-open.svg'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const { entries: worldInfoEntries, loading: worldInfoLoading } = useWorldInfo()

function handleShowChange(value: boolean) {
  emit('update:show', value)
}
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.status_bar.world_info.title')"
    style="width: 820px; max-height: 80vh; overflow-y: auto;"
  >
    <div class="world-info-card">
      <div class="world-info-note">
        <span class="world-info-note-icon" :style="{ '--icon-url': `url(${bookOpenIcon})` }" aria-hidden="true"></span>
        {{ t('game.status_bar.world_info.ai_knowledge_note') }}
      </div>

      <div v-if="worldInfoEntries.length > 0" class="world-info-list">
        <div
          v-for="entry in worldInfoEntries"
          :key="entry.id"
          class="world-info-item"
        >
          <div class="world-info-item-title">{{ entry.title }}</div>
          <div class="world-info-item-desc">{{ entry.desc }}</div>
        </div>
      </div>

      <div v-else class="world-info-empty">
        {{ worldInfoLoading ? t('common.loading') : t('game.status_bar.world_info.empty') }}
      </div>
    </div>
  </n-modal>
</template>

<style scoped>
.world-info-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.world-info-note {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: #86afe0;
  padding: 0 0 10px;
  border-bottom: 1px solid #2f2f2f;
}

.world-info-note-icon {
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

.world-info-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.world-info-item {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  column-gap: 12px;
  align-items: start;
  padding: 8px 0;
  border-bottom: 1px solid #2f2f2f;
}

.world-info-item-title {
  font-size: 15px;
  font-weight: bold;
  color: #8fc0ff;
  line-height: 1.5;
  white-space: nowrap;
}

.world-info-item-desc {
  font-size: 13px;
  line-height: 1.7;
  color: #bfd5ef;
  min-width: 0;
}

.world-info-empty {
  font-size: 13px;
  color: #8ea9c8;
  padding: 8px 0;
}

@media (max-width: 640px) {
  .world-info-item {
    grid-template-columns: 1fr;
    row-gap: 2px;
  }

  .world-info-item-title {
    white-space: normal;
  }
}
</style>
