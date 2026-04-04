<script setup lang="ts">
import { computed } from 'vue';
import { getEntityColor } from '@/utils/theme';
import type { EffectEntity } from '@/types/core';
import { useI18n } from 'vue-i18n';
import { formatEntityGrade } from '@/utils/cultivationText';
import { getEntityRowDetailLayout } from '@/utils/infoPanelLocaleConfig';

const props = defineProps<{
  item: EffectEntity;
  meta?: string; // e.g. "熟练度 50%"
  compact?: boolean;
  detailsBelow?: boolean;
}>();

defineEmits(['click']);

const { t, locale } = useI18n();

const detailLayoutMode = computed<'inline-preferred' | 'stacked'>(() => {
  return getEntityRowDetailLayout(locale.value);
});

const detailLayoutClass = computed(() => {
  return props.detailsBelow ? `details-${detailLayoutMode.value}` : null;
});
</script>

<template>
  <div 
    class="entity-row" 
    :class="[
      { 'compact': compact, 'details-below': detailsBelow },
      detailLayoutClass,
    ]"
    @click="$emit('click')"
    v-sound
  >
    <template v-if="detailsBelow">
      <div class="content">
        <div class="primary-line">
          <span class="name" :style="{ color: getEntityColor(item) }">
            {{ item.name }}
          </span>
          <span
            v-if="(meta || item.grade) && detailLayoutMode === 'inline-preferred'"
            class="info inline-info"
          >
            <span v-if="item.grade" class="grade">{{ formatEntityGrade(item.grade, t) }}</span>
            <span v-if="meta" class="meta">{{ meta }}</span>
          </span>
        </div>
        <span v-if="(meta || item.grade) && detailLayoutMode === 'stacked'" class="info details-line">
          <span v-if="item.grade" class="grade">{{ formatEntityGrade(item.grade, t) }}</span>
          <span v-if="meta" class="meta">{{ meta }}</span>
        </span>
      </div>
    </template>
    <template v-else>
      <span class="name" :style="{ color: getEntityColor(item) }">
        {{ item.name }}
      </span>
      <span class="info">
        <span v-if="meta" class="meta">{{ meta }}</span>
        <span v-if="item.grade" class="grade">{{ formatEntityGrade(item.grade, t) }}</span>
      </span>
    </template>
  </div>
</template>

<style scoped>
.entity-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.entity-row.details-below {
  display: block;
}

.entity-row:hover {
  background: rgba(255, 255, 255, 0.08);
}

.entity-row.compact {
  padding: 4px 8px;
  font-size: 12px;
}

.content {
  min-width: 0;
}

.primary-line {
  min-width: 0;
}

.info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.details-line {
  margin-top: 4px;
  justify-content: flex-start;
}

.entity-row.details-inline-preferred .primary-line {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.entity-row.details-inline-preferred .inline-info {
  justify-content: flex-start;
  flex-wrap: wrap;
}

.entity-row.details-stacked .primary-line {
  display: block;
}

.grade {
  font-size: 11px;
  padding: 0 5px;
  background: rgba(255, 215, 0, 0.15);
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: 3px;
  color: #daa520;
  line-height: 1.5;
}

.meta {
  font-size: 11px;
  color: #888;
  line-height: 1.5;
}

.entity-row.details-below.compact .details-line {
  margin-top: 2px;
}
</style>
