<script setup lang="ts">
import { computed, ref } from 'vue';
import type { SectDetail, EffectEntity } from '@/types/core';
import { useUiStore } from '@/stores/ui';
import StatItem from './components/StatItem.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import EntityRow from './components/EntityRow.vue';
import RelationRow from './components/RelationRow.vue';
import { useI18n } from 'vue-i18n';
import { formatCultivationText } from '@/utils/cultivationText';

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

function jumpToSect(id: string) {
  uiStore.select('sect', id);
}

function showDetail(item: EffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item;
  }
}

const alignmentText = props.data.alignment;

const ruleText = computed(() => {
  if (!props.data.rule_desc) {
    return t('game.info_panel.sect.no_rule');
  }
  return props.data.rule_desc;
});

const warStatusText = computed(() => (
  (props.data.war_summary?.active_war_count ?? 0) > 0
    ? t('game.sect_relations.status_war')
    : t('game.sect_relations.status_peace')
));

const strongestEnemyText = computed(() => (
  props.data.war_summary?.strongest_enemy_name || t('common.none')
));

const yearlyIncomeText = computed(() => (
  t('game.info_panel.sect.stats.income_value', {
    income: Math.floor(props.data.economy_summary?.estimated_yearly_income || 0),
  })
));

const yearlyUpkeepText = computed(() => (
  t('game.info_panel.sect.stats.upkeep_value', {
    upkeep: Math.floor(props.data.economy_summary?.estimated_yearly_upkeep || 0),
  })
));

const warWearinessText = computed(() => `${Math.max(0, Math.floor(props.data.war_weariness || 0))}/100`);

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
          <StatItem :label="t('game.info_panel.sect.stats.war_status')" :value="warStatusText" />
          <StatItem :label="t('game.info_panel.sect.stats.strongest_enemy')" :value="strongestEnemyText" />
          <StatItem :label="t('game.info_panel.sect.stats.income')" :value="yearlyIncomeText" />
          <StatItem :label="t('game.info_panel.sect.stats.upkeep')" :value="yearlyUpkeepText" />
          <StatItem :label="t('game.info_panel.sect.stats.war_weariness')" :value="warWearinessText" />
          <StatItem :label="t('game.info_panel.sect.stats.magic_stone')" :value="data.magic_stone || 0" />
       </div>

       <!-- Intro -->
       <div class="section">
          <div class="section-title">{{ t('game.info_panel.sect.sections.intro') }}</div>
          <div class="text-content">{{ data.desc }}</div>
       </div>

       <div class="section">
          <div class="section-title">{{ t('game.info_panel.sect.sections.rule') }}</div>
          <div class="text-content rule-content">{{ ruleText }}</div>
       </div>

       <div class="section" v-if="data.periodic_thinking">
          <div class="section-title">{{ t('game.info_panel.sect.sections.thinking') }}</div>
          <div class="text-content thinking-text-content">{{ data.periodic_thinking }}</div>
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
               @click="jumpToSect(item.other_sect_id)"
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
               :sub="`${formatCultivationText(m.realm, t)} · ${t('game.info_panel.avatar.stats.sect_contribution')} ${m.contribution ?? 0}`"
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
