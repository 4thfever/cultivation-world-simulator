<script setup lang="ts">
import { computed, ref } from 'vue';
import type { SectDetail, EffectEntity } from '@/types/core';
import { useUiStore } from '@/stores/ui';
import StatItem from './components/StatItem.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import EntityRow from './components/EntityRow.vue';
import RelationRow from './components/RelationRow.vue';
import { useI18n } from 'vue-i18n';

type DiplomacyItem = NonNullable<SectDetail['diplomacy_items']>[number];

const { t } = useI18n();
const props = defineProps<{
  data: SectDetail;
}>();

const uiStore = useUiStore();
const secondaryItem = ref<EffectEntity | null>(null);
const MAX_DIPLOMACY_ITEMS = 4;

function jumpToAvatar(id: string) {
  uiStore.select('avatar', id);
}

function showDetail(item: EffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item;
  }
}

const alignmentText = props.data.alignment;

const situationRows = computed(() => {
  const rows: Array<{ label: string; value: string }> = [];

  if (props.data.war_summary) {
    rows.push({
      label: t('game.info_panel.sect.situation.active_wars'),
      value: t('game.info_panel.sect.situation.active_wars_value', {
        count: props.data.war_summary.active_war_count,
      }),
    });
  }

  if (props.data.territory_summary) {
    rows.push({
      label: t('game.info_panel.sect.situation.territory'),
      value: t('game.info_panel.sect.situation.territory_value', {
        tiles: props.data.territory_summary.tile_count,
        conflicts: props.data.territory_summary.conflict_tile_count,
      }),
    });
  }

  if (props.data.economy_summary) {
    rows.push({
      label: t('game.info_panel.sect.situation.income'),
      value: t('game.info_panel.sect.situation.income_value', {
        income: Math.floor(props.data.economy_summary.controlled_tile_income),
        perTile: props.data.economy_summary.effective_income_per_tile.toFixed(1),
      }),
    });
  }

  if (props.data.war_summary?.strongest_enemy_name) {
    rows.push({
      label: t('game.info_panel.sect.situation.strongest_enemy'),
      value: t('game.info_panel.sect.situation.strongest_enemy_value', {
        name: props.data.war_summary.strongest_enemy_name,
        value: props.data.war_summary.strongest_enemy_relation,
      }),
    });
  }

  return rows;
});

const ruleText = computed(() => {
  if (!props.data.rule_desc) {
    return t('game.info_panel.sect.no_rule');
  }
  return props.data.rule_desc;
});

const simplifiedDiplomacyItems = computed(() => {
  const items = [...(props.data.diplomacy_items ?? [])];
  return items
    .sort((a, b) => {
      if (a.status === 'war' && b.status !== 'war') {
        return -1;
      }
      if (a.status !== 'war' && b.status === 'war') {
        return 1;
      }
      return (a.relation_value ?? 0) - (b.relation_value ?? 0);
    })
    .slice(0, MAX_DIPLOMACY_ITEMS);
});

function getDurationYears(months: number) {
  return Math.max(0, Math.floor((months || 0) / 12));
}

function getDiplomacyMeta(item: DiplomacyItem) {
  const statusKey = item.status === 'war'
    ? 'game.sect_relations.status_war'
    : 'game.sect_relations.status_peace';
  const relationPart = item.relation_value === undefined
    ? ''
    : t('game.info_panel.sect.diplomacy_meta_relation', { value: item.relation_value });
  return relationPart
    ? `${t(statusKey)} · ${relationPart}`
    : t(statusKey);
}

function getDiplomacySub(item: DiplomacyItem) {
  const years = getDurationYears(item.duration_months);
  const durationKey = item.status === 'war'
    ? 'game.info_panel.sect.diplomacy_war_years'
    : 'game.info_panel.sect.diplomacy_peace_years';
  return t(durationKey, { count: years });
}
</script>

<template>
  <div class="sect-detail">
    <SecondaryPopup 
      :item="secondaryItem" 
      @close="secondaryItem = null" 
    />

    <div class="content-scroll">
       <!-- Stats Grid -->
       <div class="stats-grid">
          <StatItem :label="t('game.info_panel.sect.stats.alignment')" :value="alignmentText" :class="data.alignment" />
          <StatItem 
            :label="t('game.info_panel.sect.stats.orthodoxy')" 
            :value="data.orthodoxy?.name || t('common.none')" 
            :onClick="() => showDetail(data.orthodoxy)"
          />
          <StatItem :label="t('game.info_panel.sect.stats.style')" :value="data.style" />
          <StatItem :label="t('game.info_panel.sect.stats.preferred')" :value="data.preferred_weapon || t('common.none')" />
          <StatItem :label="t('game.info_panel.sect.stats.members')" :value="data.members?.length || 0" />
          <StatItem :label="t('game.info_panel.sect.stats.total_battle_strength')" :value="Math.floor(data.total_battle_strength || 0)" />
          <StatItem :label="t('game.info_panel.sect.stats.magic_stone')" :value="data.magic_stone || 0" />
       </div>

       <!-- Intro -->
       <div class="section">
          <div class="section-title">{{ t('game.info_panel.sect.sections.intro') }}</div>
          <div class="text-content">{{ data.desc }}</div>
       </div>

       <div v-if="situationRows.length" class="section">
          <div class="section-title">{{ t('game.info_panel.sect.sections.situation') }}</div>
          <div class="situation-list">
            <div
              v-for="row in situationRows"
              :key="row.label"
              class="situation-item"
            >
              <div class="situation-label">{{ row.label }}</div>
              <div class="situation-value">{{ row.value }}</div>
            </div>
          </div>
       </div>

       <div class="section">
          <div class="section-title">{{ t('game.info_panel.sect.sections.rule') }}</div>
          <div class="text-content rule-content">{{ ruleText }}</div>
       </div>

       <div class="section" v-if="data.yearly_thinking">
          <div class="section-title">{{ t('game.info_panel.sect.sections.thinking') }}</div>
          <div class="text-content thinking-text-content">{{ data.yearly_thinking }}</div>
       </div>

       <div class="section" v-if="simplifiedDiplomacyItems.length">
          <div class="section-title">{{ t('game.info_panel.sect.sections.diplomacy') }}</div>
          <div class="list-container">
             <RelationRow
               v-for="item in simplifiedDiplomacyItems"
               :key="item.other_sect_id"
               :name="item.other_sect_name"
               :meta="getDiplomacyMeta(item)"
               :sub="getDiplomacySub(item)"
             />
          </div>
       </div>
       
       <!-- HQ -->
       <div class="section">
          <div class="section-title">{{ t('game.info_panel.sect.sections.hq', { name: data.hq_name }) }}</div>
          <div class="text-content">{{ data.hq_desc }}</div>
       </div>

       <!-- Effects -->
       <div class="section">
         <div class="section-title">{{ t('game.info_panel.sect.sections.bonus') }}</div>
         <div class="text-content highlight">{{ data.effect_desc || t('game.info_panel.sect.no_bonus') }}</div>
         <div v-if="data.runtime_effect_items?.length" class="runtime-effects-list">
            <div
              v-for="(item, idx) in data.runtime_effect_items"
              :key="`${item.source}-${idx}`"
              class="runtime-effect-item"
            >
              <div class="runtime-effect-desc">{{ item.desc }}</div>
              <div class="runtime-effect-meta">
                {{
                  item.is_permanent
                    ? t('game.info_panel.sect.runtime_effect_meta_permanent', { source: item.source_label })
                    : t('game.info_panel.sect.runtime_effect_meta', { source: item.source_label, months: item.remaining_months })
                }}
              </div>
            </div>
         </div>
         <div v-else class="runtime-effects-empty">
            {{ t('game.info_panel.sect.no_runtime_effect') }}
         </div>
       </div>

       <!-- Techniques -->
       <div class="section">
         <div class="section-title">{{ t('game.info_panel.sect.sections.techniques') }}</div>
         <div class="list-container" v-if="data.techniques?.length">
            <EntityRow 
              v-for="t in data.techniques" 
              :key="t.id" 
              :item="t"
              @click="showDetail(t)"
            />
         </div>
         <div v-else class="text-content">{{ t('common.none') }}</div>
       </div>

       <!-- Members -->
       <div class="section" v-if="data.members?.length">
          <div class="section-title">{{ t('game.info_panel.sect.sections.members') }}</div>
          <div class="list-container">
             <RelationRow 
               v-for="m in data.members" 
               :key="m.id"
               :name="m.name"
               :meta="m.rank"
               :sub="m.realm"
               @click="jumpToAvatar(m.id)"
             />
          </div>
       </div>
    </div>
  </div>
</template>

<style scoped>
.sect-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  position: relative;
}

.content-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 4px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: rgba(255, 255, 255, 0.03);
  padding: 8px;
  border-radius: 6px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-title {
  font-size: 12px;
  font-weight: bold;
  color: #666;
  border-bottom: 1px solid #333;
  padding-bottom: 4px;
  margin-bottom: 4px;
}

.text-content {
  font-size: 13px;
  line-height: 1.6;
  color: #ccc;
  white-space: pre-wrap;
}

.thinking-text-content {
  line-height: 1.5;
  white-space: normal;
}

.text-content.highlight {
  color: #e6f7ff;
  background: rgba(24, 144, 255, 0.1);
  padding: 8px;
  border-radius: 4px;
}

.runtime-effects-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.runtime-effect-item {
  padding: 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.04);
}

.runtime-effect-desc {
  font-size: 13px;
  color: #d8ecff;
  line-height: 1.5;
}

.runtime-effect-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #9fb9d6;
}

.runtime-effects-empty {
  margin-top: 8px;
  font-size: 12px;
  color: #9aa5b1;
}

.situation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.situation-item {
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.situation-label {
  font-size: 11px;
  color: #8f98a3;
  margin-bottom: 4px;
}

.situation-value {
  font-size: 13px;
  color: #e5edf5;
  line-height: 1.5;
}

.rule-content {
  color: #f3e7bf;
  background: rgba(179, 134, 0, 0.12);
  border: 1px solid rgba(179, 134, 0, 0.18);
  padding: 8px 10px;
  border-radius: 6px;
}

/* Tech List */
.tech-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tech-item {
  font-size: 13px;
  color: #eee;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s;
}

.tech-item.clickable {
  cursor: pointer;
}

.tech-item.clickable:hover {
  background: rgba(255, 255, 255, 0.1);
}

.tech-icon {
  font-size: 14px;
}
</style>
