<script setup lang="ts">
import type { RegionDetail } from '@/types/core';
import EntityRow from './components/EntityRow.vue';
import RelationRow from './components/RelationRow.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import { useI18n } from 'vue-i18n';
import { formatPopulationRatioText } from '@/utils/populationFormat';
import { useRegionDetailPanel } from '@/composables/useRegionDetailPanel';
import gemIcon from '@/assets/icons/ui/lucide/gem.svg';
import leafIcon from '@/assets/icons/ui/lucide/leaf.svg';
import messageCircleIcon from '@/assets/icons/ui/lucide/message-circle.svg';
import packageIcon from '@/assets/icons/ui/lucide/package.svg';

const { locale, t } = useI18n();
const props = defineProps<{
  data: RegionDetail;
}>();

const {
  secondaryItem,
  getPopulationBarColor,
  formatEssenceType,
  getRegionTypeExplanation,
  getRegionTypeIcon,
  showDetail,
  closeSecondaryDetail,
  jumpToSect,
  jumpToAvatar,
} = useRegionDetailPanel(() => props.data);
</script>

<template>
  <div class="region-detail">
    <SecondaryPopup 
      :item="secondaryItem" 
      @close="closeSecondaryDetail" 
    />

    <!-- Info -->
    <div class="section">
      <div class="section-title">
        <span class="section-title-icon" :style="{ '--icon-url': `url(${getRegionTypeIcon()})` }" aria-hidden="true"></span>
        {{ data.type_name }}
      </div>
      <div class="type-note">
        <span class="inline-icon" :style="{ '--icon-url': `url(${messageCircleIcon})` }" aria-hidden="true"></span>
        {{ getRegionTypeExplanation() }}
      </div>
      <div class="desc">{{ data.desc }}</div>

      <!-- Population -->
      <div class="population-container" v-if="data.population !== undefined && data.population_capacity !== undefined">
        <div class="section-title">{{ t('game.population') }}</div>
        <div class="population-bar">
          <div
            class="fill"
            :style="{
              width: `${Math.min(100, (data.population / data.population_capacity) * 100)}%`,
              backgroundColor: getPopulationBarColor(data.population / data.population_capacity),
            }"
          ></div>
          <div class="text">{{ formatPopulationRatioText(data.population, data.population_capacity, t, locale) }}</div>
        </div>
      </div>
      
      <!-- Sect Jump Button -->
      <div v-if="data.sect_id" class="actions">
         <button class="btn primary" @click="jumpToSect(data.sect_id!)">{{ t('game.info_panel.region.view_sect') }}</button>
      </div>
    </div>

    <!-- Essence -->
    <div class="section" v-if="data.essence">
      <div class="section-title">
        <span class="section-title-icon" :style="{ '--icon-url': `url(${gemIcon})` }" aria-hidden="true"></span>
        {{ t('game.info_panel.region.essence_title') }}
      </div>
      <div class="essence-info">
        {{ t('game.info_panel.region.essence_info', { type: formatEssenceType(data.essence.type), density: data.essence.density }) }}
      </div>
    </div>

    <!-- Host (洞府主人) -->
    <div class="section" v-if="data.type === 'cultivate'">
      <div class="section-title">{{ t('game.info_panel.region.sections.host') }}</div>
      <RelationRow 
        v-if="data.host"
        :name="data.host.name"
        :meta="t('game.info_panel.region.host_meta')"
        @click="jumpToAvatar(data.host.id)"
      />
      <div v-else class="empty-hint">{{ t('game.info_panel.region.no_host') }}</div>
    </div>

    <!-- Animals -->
    <div class="section" v-if="data.animals?.length">
      <div class="section-title">{{ t('game.info_panel.region.sections.animals') }}</div>
      <div class="list">
        <EntityRow 
          v-for="animal in data.animals"
          :key="animal.name"
          :item="animal"
          compact
          @click="showDetail(animal)"
        />
      </div>
    </div>

    <!-- Plants -->
    <div class="section" v-if="data.plants?.length">
      <div class="section-title">
        <span class="section-title-icon" :style="{ '--icon-url': `url(${leafIcon})` }" aria-hidden="true"></span>
        {{ t('game.info_panel.region.sections.plants') }}
      </div>
      <div class="list">
        <EntityRow 
          v-for="plant in data.plants"
          :key="plant.name"
          :item="plant"
          compact
          @click="showDetail(plant)"
        />
      </div>
    </div>

    <!-- Lodes -->
    <div class="section" v-if="data.lodes?.length">
      <div class="section-title">
        <span class="section-title-icon" :style="{ '--icon-url': `url(${gemIcon})` }" aria-hidden="true"></span>
        {{ t('game.info_panel.region.sections.lodes') }}
      </div>
      <div class="list">
        <EntityRow 
          v-for="lode in data.lodes"
          :key="lode.name"
          :item="lode"
          compact
          @click="showDetail(lode)"
        />
      </div>
    </div>

    <!-- Store Items -->
    <div class="section" v-if="data.store_items?.length">
      <div class="section-title">
        <span class="section-title-icon" :style="{ '--icon-url': `url(${packageIcon})` }" aria-hidden="true"></span>
        {{ t('game.info_panel.region.sections.market') }}
      </div>
      <div class="list">
        <EntityRow 
          v-for="item in data.store_items"
          :key="item.id || item.name"
          :item="item"
          :meta="t('game.info_panel.region.price_meta', { price: item.price })"
          compact
          @click="showDetail(item)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.region-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  overflow-y: auto;
  position: relative;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: bold;
  color: #666;
  text-transform: uppercase;
  border-bottom: 1px solid #333;
  padding-bottom: 4px;
}

.desc {
  font-size: 13px;
  line-height: 1.5;
  color: #ccc;
}

.type-note {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: #a8d8c0;
  line-height: 1.5;
}

.section-title-icon,
.inline-icon {
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

.essence-info {
  font-size: 13px;
  color: #88fdc4;
}

.empty-hint {
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.actions {
  margin-top: 8px;
}

.btn {
  width: 100%;
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: #ccc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn.primary {
  background: #177ddc;
  color: white;
  border: none;
}

.btn.primary:hover {
  background: #1890ff;
}

.population-container {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.population-bar {
  height: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.population-bar .fill {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.population-bar .text {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: white;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
}
</style>
