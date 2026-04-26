<script setup lang="ts">
import { NModal, NTable, NTag, NSpin } from 'naive-ui';
import { useI18n } from 'vue-i18n';
import { useSectRelationsModal } from '@/composables/useSectRelationsModal';

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
}>();

const { t } = useI18n();
const handleShowChange = (val: boolean) => {
  emit('update:show', val);
};
const {
  loading,
  panelStyleVars,
  sortedRelations,
  getValueColor,
  getDeltaColor,
  formatDelta,
  getValueLabelKey,
  resolveReasonLabel,
  resolveDiplomacyStatus,
  openSectInfo,
} = useSectRelationsModal(() => props.show, () => handleShowChange(false));
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.sect_relations.title')"
    style="width: 800px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="loading">
      <div class="sect-relations-panel" :style="panelStyleVars">
      <n-table :bordered="false" :single-line="false" size="small">
        <thead>
          <tr>
            <th>{{ t('game.sect_relations.sect_a') }}</th>
            <th>{{ t('game.sect_relations.sect_b') }}</th>
            <th>{{ t('game.sect_relations.status') }}</th>
            <th>{{ t('game.sect_relations.value') }}</th>
            <th>{{ t('game.sect_relations.reasons') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in sortedRelations" :key="`${item.sect_a_id}-${item.sect_b_id}`">
            <td>
              <a class="clickable-text" @click="openSectInfo(item.sect_a_id)">{{ item.sect_a_name }}</a>
            </td>
            <td>
              <a class="clickable-text" @click="openSectInfo(item.sect_b_id)">{{ item.sect_b_name }}</a>
            </td>
            <td>
              <span
                :style="{ color: item.diplomacy_status === 'war' ? '#ff7875' : '#95de64', fontWeight: 500 }"
              >
                {{ resolveDiplomacyStatus(item) }}
              </span>
            </td>
            <td>
              <span :style="{ color: getValueColor(item.value), fontWeight: 500 }">
                {{ item.value }}
              </span>
              <span class="value-label">{{ t(`game.sect_relations.${getValueLabelKey(item.value)}`) }}</span>
            </td>
            <td>
              <n-tag
                v-for="(reasonItem, index) in item.reason_breakdown"
                :key="`${item.sect_a_id}-${item.sect_b_id}-${reasonItem.reason}-${index}`"
                v-show="resolveReasonLabel(reasonItem)"
                size="small"
                :bordered="false"
                style="margin-right: 4px; margin-bottom: 2px"
                class="reason-tag"
              >
                <span class="reason-text">{{ resolveReasonLabel(reasonItem) }}</span>
                <span class="delta-text" :style="{ color: getDeltaColor(reasonItem.delta) }">
                  {{ formatDelta(reasonItem.delta) }}
                </span>
              </n-tag>
            </td>
          </tr>
          <tr v-if="!sortedRelations.length">
            <td colspan="5" class="empty-cell">
              {{ t('game.sect_relations.empty') }}
            </td>
          </tr>
        </tbody>
      </n-table>
      </div>
    </n-spin>
  </n-modal>
</template>

<style scoped>
.clickable-text {
  color: var(--panel-link);
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s;
}

.clickable-text:hover {
  color: var(--panel-link-hover);
  text-decoration: underline;
}

:deep(.n-table th) {
  color: var(--panel-text-secondary);
}

.value-label {
  margin-left: 6px;
  font-size: 0.9em;
  opacity: 0.9;
  color: var(--panel-text-secondary);
}

.reason-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--panel-accent-soft);
}

.reason-text {
  color: var(--panel-text-primary);
}

.delta-text {
  font-weight: 700;
}

.empty-cell {
  text-align: center;
  color: var(--panel-empty);
}
</style>

