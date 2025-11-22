<script setup lang="ts">
import { ref } from 'vue';
import type { RegionDetail, EffectEntity } from '@/types/core';
import EntityRow from './components/EntityRow.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import { translateElement } from '@/utils/formatters/dictionary';

defineProps<{
  data: RegionDetail;
}>();

const secondaryItem = ref<EffectEntity | null>(null);

function showDetail(item: EffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item;
  }
}
</script>

<template>
  <div class="region-detail">
    <SecondaryPopup 
      :item="secondaryItem" 
      @close="secondaryItem = null" 
    />

    <!-- Info -->
    <div class="section">
      <div class="section-title">{{ data.type_name }}</div>
      <div class="desc">{{ data.desc }}</div>
    </div>

    <!-- Essence -->
    <div class="section" v-if="data.essence">
      <div class="section-title">灵气环境</div>
      <div class="essence-info">
        {{ translateElement(data.essence.type) }}行灵气 · 浓度 {{ data.essence.density }}
      </div>
    </div>

    <!-- Animals -->
    <div class="section" v-if="data.animals?.length">
      <div class="section-title">动物分布</div>
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
      <div class="section-title">植物分布</div>
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

.essence-info {
  font-size: 13px;
  color: #88fdc4;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
