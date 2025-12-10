<script setup lang="ts">
import { ref } from 'vue';
import type { RegionDetail, EffectEntity } from '@/types/core';
import EntityRow from './components/EntityRow.vue';
import RelationRow from './components/RelationRow.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import { useUiStore } from '@/stores/ui';

defineProps<{
  data: RegionDetail;
}>();

const uiStore = useUiStore();
const secondaryItem = ref<EffectEntity | null>(null);

function showDetail(item: EffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item;
  }
}

function jumpToSect(id: number) {
  uiStore.select('sect', id.toString());
}

function jumpToAvatar(id: string) {
  uiStore.select('avatar', id);
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
      
      <!-- Sect Jump Button -->
      <div v-if="data.sect_id" class="actions">
         <button class="btn primary" @click="jumpToSect(data.sect_id!)">查看宗门详情</button>
      </div>
    </div>

    <!-- Essence -->
    <div class="section" v-if="data.essence">
      <div class="section-title">灵气环境</div>
      <div class="essence-info">
        {{ data.essence.type }}行灵气 · 浓度 {{ data.essence.density }}
      </div>
    </div>

    <!-- Host (洞府主人) -->
    <div class="section" v-if="data.type === 'cultivate'">
      <div class="section-title">洞府主人</div>
      <RelationRow 
        v-if="data.host"
        :name="data.host.name"
        meta="主人"
        @click="jumpToAvatar(data.host.id)"
      />
      <div v-else class="empty-hint">无主（可占据）</div>
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
</style>
