<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { NModal, NTable, NTag, NSpin } from 'naive-ui';
import { useI18n } from 'vue-i18n';
import { worldApi } from '@/api';
import { SHARED_UI_COLORS, SYSTEM_PANEL_THEMES } from '@/constants/uiColors';
import { useUiStore } from '../../../stores/ui';
import type { SectRelationDTO } from '../../../types/api';
import { logError } from '@/utils/appError';

const props = defineProps<{
  show: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void;
}>();

const { t } = useI18n();
const uiStore = useUiStore();
const sectTheme = SYSTEM_PANEL_THEMES.sectRelations
const panelStyleVars = {
  '--panel-accent': sectTheme.accent,
  '--panel-accent-strong': sectTheme.accentStrong,
  '--panel-accent-soft': sectTheme.accentSoft,
  '--panel-link': sectTheme.link,
  '--panel-link-hover': sectTheme.linkHover,
  '--panel-title': sectTheme.title,
  '--panel-empty': sectTheme.empty,
  '--panel-border': sectTheme.border,
  '--panel-text-primary': SHARED_UI_COLORS.textPrimary,
  '--panel-text-secondary': SHARED_UI_COLORS.textSecondary,
}

const loading = ref(false);
const relations = ref<SectRelationDTO[]>([]);

const sortedRelations = computed(() => {
  // 敌对程度高（数值更低）的排在前面
  return [...relations.value].sort((a, b) => a.value - b.value);
});

const getValueColor = (value: number) => {
  if (value <= -50) return SHARED_UI_COLORS.dangerSoft;
  if (value < 0) return '#d8a14a';
  if (value >= 50) return SHARED_UI_COLORS.successSoft;
  if (value > 0) return '#b6df89';
  return '#d9d9d9';
};

const getDeltaColor = (delta: number) => {
  if (delta > 0) return SHARED_UI_COLORS.successStrong;
  if (delta < 0) return SHARED_UI_COLORS.dangerStrong;
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
  if (item.reason === 'PEACE_STATE') {
    return '';
  }
  if (item.reason === 'LONG_PEACE') {
    return baseLabel;
  }
  if (item.reason === 'RANDOM_EVENT') {
    const cause = item.meta?.cause;
    if (typeof cause === 'string' && cause.trim()) {
      return `${baseLabel} (${cause.trim()})`;
    }
    return baseLabel;
  }

  if (item.reason !== 'TERRITORY_CONFLICT') {
    if (item.reason === 'WAR_STATE' || item.reason === 'PEACE_STATE' || item.reason === 'LONG_PEACE') {
      const months = item.meta?.war_months ?? item.meta?.peace_months
      if (typeof months === 'number' && months > 0) {
        return `${baseLabel} (${t('game.sect_relations.duration_months', { count: months })})`
      }
    }
    return baseLabel;
  }

  const borderContactEdges = item.meta?.border_contact_edges ?? item.meta?.overlap_tiles;
  if (typeof borderContactEdges !== 'number') {
    return baseLabel;
  }

  return `${baseLabel} (${t('game.sect_relations.overlap_tiles', { count: borderContactEdges })})`;
};

const resolveDiplomacyStatus = (item: SectRelationDTO) => {
  const key = item.diplomacy_status === 'war'
    ? 'game.sect_relations.status_war'
    : 'game.sect_relations.status_peace';
  return `${t(key)} · ${t('game.sect_relations.duration_months', { count: item.diplomacy_duration_months })}`;
};

const openSectInfo = (id: number) => {
  uiStore.select('sect', String(id));
  handleShowChange(false);
};

const fetchRelations = async () => {
  loading.value = true;
  try {
    const res = await worldApi.fetchSectRelations();
    relations.value = res.relations ?? [];
  } catch (e) {
    logError('SectRelationsModal fetch relations', e);
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

