<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { NModal, NTable, NTag, NSpin } from 'naive-ui';
import { useI18n } from 'vue-i18n';
import { worldApi } from '@/api';
import { useUiStore } from '../../../stores/ui';
import type { SectRelationDTO } from '../../../types/api';

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
}>();

const { t } = useI18n();
const uiStore = useUiStore();

const loading = ref(false);
const relations = ref<SectRelationDTO[]>([]);

const sortedRelations = computed(() => {
  // 敌对程度高（数值更低）的排在前面
  return [...relations.value].sort((a, b) => a.value - b.value);
});

const getValueColor = (value: number) => {
  if (value <= -50) return '#ff4d4f';
  if (value < 0) return '#fa8c16';
  if (value >= 50) return '#52c41a';
  if (value > 0) return '#a0d911';
  return '#d9d9d9';
};

const getDeltaColor = (delta: number) => {
  if (delta > 0) return '#52c41a';
  if (delta < 0) return '#ff4d4f';
  return '#d9d9d9';
};

const formatDelta = (delta: number): string => {
  if (delta > 0) return `+${delta}`;
  return `${delta}`;
};

/** 根据关系值返回多语言标签 key 后缀（与 i18n value_label_* 对应），极恶/极善阈值为 ±50 */
const getValueLabelKey = (value: number): string => {
  if (value <= -50) return 'value_label_very_hostile';
  if (value < 0) return 'value_label_hostile';
  if (value === 0) return 'value_label_neutral';
  if (value < 50) return 'value_label_friendly';
  return 'value_label_very_friendly';
};

const resolveReasonLabel = (item: SectRelationDTO['reason_breakdown'][number]) => {
  const baseLabel = t(`game.sect_relations.reasons_map.${item.reason}`);
  if (item.reason === 'RANDOM_EVENT') {
    const cause = item.meta?.cause;
    if (typeof cause === 'string' && cause.trim()) {
      return `${baseLabel} (${cause.trim()})`;
    }
    return baseLabel;
  }

  if (item.reason !== 'TERRITORY_CONFLICT') {
    return baseLabel;
  }

  const overlapTiles = item.meta?.overlap_tiles;
  if (typeof overlapTiles !== 'number') {
    return baseLabel;
  }

  return `${baseLabel} (${t('game.sect_relations.overlap_tiles', { count: overlapTiles })})`;
};

const openSectInfo = (id: number) => {
  uiStore.select('sect', id);
  handleShowChange(false);
};

const fetchRelations = async () => {
  loading.value = true;
  try {
    const res = await worldApi.fetchSectRelations();
    relations.value = res.relations ?? [];
  } catch (e) {
    console.error(e);
    relations.value = [];
  } finally {
    loading.value = false;
  }
};

const handleShowChange = (val: boolean) => {
  emit('update:show', val);
};

watch(
  () => props.show,
  (newVal) => {
    if (newVal) {
      fetchRelations();
    }
  },
);
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
      <n-table :bordered="false" :single-line="false" size="small">
        <thead>
          <tr>
            <th>{{ t('game.sect_relations.sect_a') }}</th>
            <th>{{ t('game.sect_relations.sect_b') }}</th>
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
              <span :style="{ color: getValueColor(item.value), fontWeight: 500 }">
                {{ item.value }}
              </span>
              <span class="value-label">{{ t(`game.sect_relations.${getValueLabelKey(item.value)}`) }}</span>
            </td>
            <td>
              <n-tag
                v-for="(reasonItem, index) in item.reason_breakdown"
                :key="`${item.sect_a_id}-${item.sect_b_id}-${reasonItem.reason}-${index}`"
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
            <td colspan="4" style="text-align: center; color: #888;">
              {{ t('game.sect_relations.empty') }}
            </td>
          </tr>
        </tbody>
      </n-table>
    </n-spin>
  </n-modal>
</template>

<style scoped>
.clickable-text {
  color: #4dabf7;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s;
}

.clickable-text:hover {
  color: #8bc6ff;
  text-decoration: underline;
}

.value-label {
  margin-left: 6px;
  font-size: 0.9em;
  opacity: 0.9;
}

.reason-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.reason-text {
  color: #d9d9d9;
}

.delta-text {
  font-weight: 700;
}
</style>

