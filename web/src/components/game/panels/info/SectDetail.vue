<script setup lang="ts">
import { ref } from 'vue';
import type { SectDetail, EffectEntity } from '@/types/core';
import { useUiStore } from '@/stores/ui';
import StatItem from './components/StatItem.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import EntityRow from './components/EntityRow.vue';
import RelationRow from './components/RelationRow.vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps<{
  data: SectDetail;
}>();

const uiStore = useUiStore();
const secondaryItem = ref<EffectEntity | null>(null);

function jumpToAvatar(id: string) {
  uiStore.select('avatar', id);
}

function showDetail(item: EffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item;
  }
}

const alignmentText = props.data.alignment;
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
       </div>

       <!-- Intro -->
       <div class="section">
          <div class="section-title">{{ t('game.info_panel.sect.sections.intro') }}</div>
          <div class="text-content">{{ data.desc }}</div>
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

.text-content.highlight {
  color: #e6f7ff;
  background: rgba(24, 144, 255, 0.1);
  padding: 8px;
  border-radius: 4px;
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
