<script setup lang="ts">
import type { EffectEntity } from '@/types/core';
import { getEntityColor, getEntityGradeTone } from '@/utils/theme';
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { formatAttributeLabel, formatEntityGrade } from '@/utils/cultivationText';

const { t } = useI18n();

const props = defineProps<{
  item: EffectEntity | null;
  emptyLabel?: string;
  showName?: boolean;
}>();

const displayType = computed(() => {
  if (props.item?.type_name) return props.item.type_name;
  if (!props.item?.type) return '';
  return t(`game.info_panel.popup.types.${props.item.type}`) || props.item.type;
});

const displayGrade = computed(() => {
  return formatEntityGrade(props.item?.grade || props.item?.rarity, t);
});

const gradeBadgeClass = computed(() => {
  return `grade-${getEntityGradeTone(props.item?.grade || props.item?.rarity)}`;
});

const displayAttribute = computed(() => {
  return formatAttributeLabel(props.item?.attribute, t);
});

const displayDescription = computed(() => {
  return props.item?.desc || '';
});
</script>

<template>
  <div class="entity-detail-card">
    <template v-if="item">
      <div class="sec-row" v-if="displayGrade || displayType || displayAttribute">
        <span v-if="displayGrade" class="badge grade-badge" :class="gradeBadgeClass">{{ displayGrade }}</span>
        <span v-if="displayType" class="badge type-badge">{{ displayType }}</span>
        <span v-if="displayAttribute" class="badge attr-badge">{{ displayAttribute }}</span>
      </div>

      <div v-if="showName !== false" class="sec-title" :style="{ color: getEntityColor(item) }">
        {{ item.name }}
      </div>

      <div class="sec-desc" v-if="displayDescription">{{ displayDescription }}</div>

      <div v-if="item.effect_desc" class="effect-box">
        <div class="label">{{ t('game.info_panel.popup.effect') }}</div>
        <div class="effect-text">{{ item.effect_desc }}</div>
      </div>

      <div v-if="item.drops?.length" class="drops-box">
        <div class="label">{{ t('game.info_panel.popup.drops') }}</div>
        <div class="drop-list">
          <span 
            v-for="drop in item.drops" 
            :key="drop.id" 
            class="drop-tag"
            :style="{ color: getEntityColor(drop) }"
          >
            {{ drop.name }}
          </span>
        </div>
      </div>

      <div v-if="item.hq_name" class="extra-info">
        <div><strong>{{ t('game.info_panel.popup.hq') }}</strong> {{ item.hq_name }}</div>
        <div class="sub-desc">{{ item.hq_desc }}</div>
      </div>
    </template>

    <div v-else class="empty-state">
      {{ emptyLabel || t('common.none') }}
    </div>
  </div>
</template>

<style scoped>
.entity-detail-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 13px;
  color: #ccc;
}

.sec-title {
  font-size: 15px;
  font-weight: bold;
}

.badge {
  display: inline-block;
  padding: 2px 6px;
  background: #444;
  border-radius: 4px;
  font-size: 11px;
  color: #fff;
}

.sec-row {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.grade-badge {
  background: rgba(255, 215, 0, 0.2);
  border: 1px solid rgba(255, 215, 0, 0.4);
  color: #daa520;
}

.grade-badge.grade-epic {
  background: rgba(196, 136, 253, 0.18);
  border: 1px solid rgba(196, 136, 253, 0.42);
  color: #d7b6ff;
}

.grade-badge.grade-legendary {
  background: rgba(255, 215, 0, 0.2);
  border: 1px solid rgba(255, 215, 0, 0.4);
  color: #daa520;
}

.type-badge {
  background: rgba(100, 149, 237, 0.2);
  border: 1px solid rgba(100, 149, 237, 0.4);
  color: #87ceeb;
}

.attr-badge {
  background: rgba(89, 168, 124, 0.18);
  border: 1px solid rgba(89, 168, 124, 0.35);
  color: #9fd8b1;
}

.sec-desc {
  line-height: 1.5;
  color: #bbb;
}

.effect-box {
  background: rgba(0, 0, 0, 0.2);
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #444;
}

.label {
  font-size: 11px;
  color: #888;
  margin-bottom: 4px;
}

.effect-text {
  color: #ffd700;
  font-size: 12px;
  line-height: 1.4;
}

.extra-info {
  border-top: 1px solid #444;
  padding-top: 8px;
  font-size: 12px;
}

.sub-desc {
  color: #888;
  margin-top: 2px;
}

.drops-box {
  margin-top: 4px;
}

.drop-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.drop-tag {
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 11px;
}

.empty-state {
  color: #888;
  font-size: 12px;
  line-height: 1.5;
}
</style>
