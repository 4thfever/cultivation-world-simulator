<script setup lang="ts">
import { ref } from 'vue';
import type { AvatarDetail, EffectEntity } from '@/types/core';
import { formatHp, formatAge } from '@/utils/formatters/number';
import StatItem from './components/StatItem.vue';
import EntityRow from './components/EntityRow.vue';
import TagList from './components/TagList.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import { gameApi } from '@/api/game';
import { useUiStore } from '@/stores/ui';

const props = defineProps<{
  data: AvatarDetail;
}>();

const uiStore = useUiStore();
const secondaryItem = ref<EffectEntity | null>(null);
const showObjectiveModal = ref(false);
const objectiveContent = ref('');

// --- Actions ---

function showDetail(item: EffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item;
  }
}

function jumpToAvatar(id: string) {
  uiStore.select('avatar', id);
}

async function handleSetObjective() {
  if (!objectiveContent.value.trim()) return;
  try {
    await gameApi.setLongTermObjective(props.data.id, objectiveContent.value);
    showObjectiveModal.value = false;
    objectiveContent.value = '';
    uiStore.refreshDetail();
  } catch (e) {
    console.error(e);
    alert('设定失败');
  }
}

async function handleClearObjective() {
  if (!confirm('确定要清空该角色的长期目标吗？')) return;
  try {
    await gameApi.clearLongTermObjective(props.data.id);
    uiStore.refreshDetail();
  } catch (e) {
    console.error(e);
  }
}
</script>

<template>
  <div class="avatar-detail">
    <SecondaryPopup 
      :item="secondaryItem" 
      @close="secondaryItem = null" 
    />

    <!-- Actions Bar -->
    <div class="actions-bar">
      <button class="btn primary" @click="showObjectiveModal = true">设定目标</button>
      <button class="btn" @click="handleClearObjective">清空目标</button>
    </div>

    <div class="content-scroll">
      <!-- Stats Grid -->
      <div class="stats-grid">
        <StatItem label="境界" :value="data.realm" :sub-value="data.level" />
        <StatItem label="年龄" :value="formatAge(data.age, data.lifespan)" />
        
        <StatItem label="HP" :value="formatHp(data.hp.cur, data.hp.max)" />
        <StatItem label="MP" :value="formatHp(data.mp.cur, data.mp.max)" />
        
        <StatItem 
          label="阵营" 
          :value="data.alignment" 
          :on-click="() => showDetail(data.alignment_detail)"
        />
        <StatItem 
          label="宗门" 
          :value="data.sect?.name || '散修'" 
          :sub-value="data.sect?.rank"
          :on-click="data.sect ? () => showDetail(data.sect) : undefined"
        />
        
        <StatItem 
          label="灵根" 
          :value="data.root" 
          :on-click="() => showDetail(data.root_detail)"
        />
        <StatItem label="灵石" :value="data.magic_stone" />
      </div>

      <!-- Thinking -->
      <div class="section" v-if="data.thinking">
        <div class="section-title">当前思考</div>
        <div class="text-content">{{ data.thinking }}</div>
      </div>

      <!-- Personas -->
      <div class="section" v-if="data.personas?.length">
        <div class="section-title">特质</div>
        <TagList :tags="data.personas" @click="showDetail" />
      </div>

      <!-- Equipment & Sect -->
      <div class="section">
        <div class="section-title">功法与装备</div>
        <EntityRow 
          v-if="data.technique" 
          :item="data.technique" 
          @click="showDetail(data.technique)" 
        />
        <EntityRow 
          v-if="data.weapon" 
          :item="data.weapon" 
          :meta="`熟练度 ${data.weapon.proficiency}`"
          @click="showDetail(data.weapon)" 
        />
        <EntityRow 
          v-if="data.auxiliary" 
          :item="data.auxiliary" 
          @click="showDetail(data.auxiliary)" 
        />
         <EntityRow 
          v-if="data.spirit_animal" 
          :item="data.spirit_animal" 
          @click="showDetail(data.spirit_animal)" 
        />
      </div>

      <!-- Items -->
      <div class="section" v-if="data.items?.length">
        <div class="section-title">物品</div>
        <div class="list-container">
          <EntityRow 
            v-for="item in data.items"
            :key="item.name"
            :item="item"
            :meta="`x${item.count}`"
            compact
            @click="showDetail(item)"
          />
        </div>
      </div>

      <!-- Relations -->
      <div class="section" v-if="data.relations?.length">
        <div class="section-title">关系</div>
        <div class="list-container">
          <div 
            v-for="rel in data.relations"
            :key="rel.target_id"
            class="relation-item"
            @click="jumpToAvatar(rel.target_id)"
          >
            <div class="rel-head">
              <span class="rel-name">{{ rel.name }}</span>
              <span class="rel-type">{{ rel.relation }}</span>
            </div>
            <div class="rel-sub">{{ rel.sect }} · {{ rel.realm }}</div>
          </div>
        </div>
      </div>

      <!-- Objectives -->
      <div class="section">
        <div class="section-title">长期目标</div>
        <div class="text-content">{{ data.long_term_objective || '无' }}</div>
      </div>
      <div class="section">
        <div class="section-title">短期目标</div>
        <div class="text-content">{{ data.short_term_objective || '无' }}</div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showObjectiveModal" class="modal-overlay">
      <div class="modal">
        <h3>设定长期目标</h3>
        <textarea v-model="objectiveContent" placeholder="请输入目标..."></textarea>
        <div class="modal-footer">
          <button class="btn primary" @click="handleSetObjective">确认</button>
          <button class="btn" @click="showObjectiveModal = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.avatar-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0; /* Ensure flex child scrolling works */
  position: relative; /* For secondary popup */
}

.actions-bar {
  display: flex;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid #333;
  margin-bottom: 12px;
}

.content-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 4px; /* Space for scrollbar */
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
  line-height: 1.5;
  color: #ccc;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* Buttons */
.btn {
  flex: 1;
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

/* Relations */
.relation-item {
  padding: 6px 8px;
  background: rgba(0, 0, 0, 0.2);
  border-left: 2px solid #333;
  cursor: pointer;
  transition: all 0.2s;
}

.relation-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-left-color: #666;
}

.rel-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2px;
}

.rel-name {
  font-size: 13px;
  color: #eee;
  font-weight: bold;
}

.rel-type {
  font-size: 12px;
  color: #aaa;
}

.rel-sub {
  font-size: 11px;
  color: #666;
}

/* Modal */
.modal-overlay {
  position: absolute;
  top: 0;
  left: -16px;
  right: -16px;
  bottom: -16px;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  width: 280px;
  background: #222;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal h3 {
  margin: 0;
  font-size: 14px;
  color: #ddd;
}

.modal textarea {
  height: 100px;
  background: #111;
  border: 1px solid #444;
  color: #eee;
  padding: 8px;
  resize: none;
}

.modal-footer {
  display: flex;
  gap: 10px;
}
</style>
