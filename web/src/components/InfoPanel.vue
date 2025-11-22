<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useGameStore } from '../stores/game'
import type { IEffectEntity } from '../types/game'

const store = useGameStore()
const panelRef = ref<HTMLElement | null>(null)
let lastOpenAt = 0

const showObjectiveModal = ref(false)
const objectiveContent = ref('')

// Secondary info state
const secondaryItem = ref<IEffectEntity | null>(null)

const title = computed(() => {
  if (store.detailInfo && !store.detailInfo.fallback) {
    return store.detailInfo.name
  }
  return store.selectedTarget?.name ?? ''
})

watch(
  () => store.selectedTarget,
  (target) => {
    showObjectiveModal.value = false
    objectiveContent.value = ''
    secondaryItem.value = null
    if (target) {
      lastOpenAt = performance.now()
    }
  }
)

function handleDocumentPointerDown(event: PointerEvent) {
  if (!store.selectedTarget || !panelRef.value) return
  const target = event.target as Node | null
  if (target && panelRef.value.contains(target)) return

  const now = performance.now()
  if (now - lastOpenAt < 50) {
    return
  }
  store.closeInfoPanel()
}

async function handleSetObjective() {
  if (!store.selectedTarget || !objectiveContent.value.trim()) return
  await store.setLongTermObjective(store.selectedTarget.id, objectiveContent.value)
  showObjectiveModal.value = false
  objectiveContent.value = ''
}

async function handleClearObjective() {
  if (!store.selectedTarget) return
  if (confirm('确定要清空该角色的长期目标吗？（系统将在之后自动重新生成）')) {
    await store.clearLongTermObjective(store.selectedTarget.id)
  }
}

function showSecondary(item: IEffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item
  }
}

function jumpToAvatar(id: string) {
  store.openInfoPanel({ type: 'avatar', id })
}

// Helper for colors
function getRarityColor(item: any) {
    if (!item) return undefined
    if (item.color && Array.isArray(item.color) && item.color.length === 3) {
        const [r, g, b] = item.color
        return `rgb(${r},${g},${b})`
    }
    // Map grade string to color if no color prop
    const grade = item.grade || item.rarity
    if (!grade) return undefined
    if (['上品', '宝物', 'SR', 'Upper'].some(s => grade.includes(s))) return '#c488fd' // Purple
    if (['中品', 'R', 'Middle'].some(s => grade.includes(s))) return '#88fdc4' // Green? Usually blue
    if (['法宝', 'SSR', 'Artifact'].some(s => grade.includes(s))) return '#fddc88' // Gold
    return undefined
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
})
</script>

<template>
  <div
    v-if="store.selectedTarget"
    class="info-panel"
    ref="panelRef"
  >
    <!-- Secondary Panel (Popup) -->
    <div v-if="secondaryItem" class="secondary-panel">
      <div class="sec-header">
        <span class="sec-title" :style="{ color: getRarityColor(secondaryItem) }">{{ secondaryItem.name }}</span>
        <button class="close-btn-small" @click="secondaryItem = null">×</button>
      </div>
      <div class="sec-body">
         <div class="sec-row" v-if="secondaryItem.grade || secondaryItem.rarity">
            <span class="tag">{{ secondaryItem.grade || secondaryItem.rarity }}</span>
         </div>
         <div class="sec-desc">{{ secondaryItem.desc }}</div>
         <div v-if="secondaryItem.effect_desc" class="sec-effect-box">
            <div class="sec-label">效果：</div>
            <div class="sec-effect-text">{{ secondaryItem.effect_desc }}</div>
         </div>
         
         <!-- 特殊字段展示 -->
         <div v-if="secondaryItem.hq_name" class="sec-extra">
            <div><strong>驻地:</strong> {{ secondaryItem.hq_name }}</div>
            <div class="sub-desc">{{ secondaryItem.hq_desc }}</div>
         </div>
      </div>
    </div>

    <div class="panel-actions" v-if="store.selectedTarget.type === 'avatar'">
      <button class="action-btn primary" @click="showObjectiveModal = true">设定长期目标</button>
      <button class="action-btn secondary" @click="handleClearObjective">清空长期目标</button>
    </div>

    <button class="close-btn-absolute" type="button" @click="store.closeInfoPanel()">×</button>

    <div class="info-header">
      <div class="info-title">{{ title || '详情' }}</div>
      <div class="header-right">
         <span v-if="store.detailInfo && !store.detailInfo.fallback" class="header-subtitle">{{ store.detailInfo.nickname || '' }}</span>
      </div>
    </div>

    <div class="info-body">
      <div v-if="store.infoLoading" class="placeholder">加载中...</div>
      <div v-else-if="store.infoError" class="placeholder error">
        {{ store.infoError }}
      </div>
      
      <!-- 结构化数据展示 -->
      <div v-else-if="store.detailInfo && !store.detailInfo.fallback && store.selectedTarget.type === 'avatar'" class="structured-content">
          <!-- 基础属性 -->
          <div class="stats-grid">
             <div class="stat-item">
                <label>境界</label>
                <span>{{ store.detailInfo.realm }} ({{ store.detailInfo.level }})</span>
             </div>
             <div class="stat-item">
                <label>年龄</label>
                <span>{{ store.detailInfo.age }} / {{ store.detailInfo.lifespan }}</span>
             </div>
             <div class="stat-item">
                <label>HP</label>
                <span>{{ Math.floor(store.detailInfo.hp.cur) }}/{{ store.detailInfo.hp.max }}</span>
             </div>
             <div class="stat-item">
                <label>灵石</label>
                <span>{{ store.detailInfo.magic_stone }}</span>
             </div>
             <div 
                class="stat-item full clickable" 
                @click="showSecondary(store.detailInfo.alignment_detail)"
                v-if="store.detailInfo.alignment_detail"
             >
                <label>阵营</label>
                <span>{{ store.detailInfo.alignment }}</span>
             </div>
             <div class="stat-item full" v-else>
                <label>阵营</label>
                <span>{{ store.detailInfo.alignment }}</span>
             </div>

             <div 
                class="stat-item full clickable" 
                @click="showSecondary(store.detailInfo.root_detail)"
                v-if="store.detailInfo.root_detail"
             >
                <label>灵根</label>
                <span>{{ store.detailInfo.root }}</span>
             </div>
             <div class="stat-item full" v-else>
                <label>灵根</label>
                <span>{{ store.detailInfo.root }}</span>
             </div>
          </div>

          <!-- 状态 -->
          <div class="section" v-if="store.detailInfo.thinking">
              <div class="section-title">当前思考</div>
              <div class="text-content">{{ store.detailInfo.thinking }}</div>
          </div>
          
          <!-- 特质 -->
          <div class="section" v-if="store.detailInfo.personas?.length">
             <div class="section-title">特质</div>
             <div class="tags-container">
                <span 
                  v-for="p in store.detailInfo.personas" 
                  :key="p.name" 
                  class="clickable-tag"
                  :style="{ borderColor: getRarityColor(p) }"
                  @click="showSecondary(p)"
                >
                   {{ p.name }}
                </span>
             </div>
          </div>

          <!-- 功法 -->
          <div class="section" v-if="store.detailInfo.technique">
             <div class="section-title">功法</div>
             <div class="clickable-item" @click="showSecondary(store.detailInfo.technique)">
                <span :style="{ color: getRarityColor(store.detailInfo.technique) }">{{ store.detailInfo.technique.name }}</span>
                <span class="item-meta">{{ store.detailInfo.technique.grade }}</span>
             </div>
          </div>
          
          <!-- 宗门 -->
          <div class="section" v-if="store.detailInfo.sect">
             <div class="section-title">宗门</div>
             <div class="clickable-item" @click="showSecondary(store.detailInfo.sect)">
                <span>{{ store.detailInfo.sect.name }}</span>
                <span class="item-meta">{{ store.detailInfo.sect.rank }}</span>
             </div>
          </div>

          <!-- 装备 -->
          <div class="section" v-if="store.detailInfo.weapon || store.detailInfo.auxiliary">
             <div class="section-title">装备</div>
             <div v-if="store.detailInfo.weapon" class="clickable-item" @click="showSecondary(store.detailInfo.weapon)">
                <span :style="{ color: getRarityColor(store.detailInfo.weapon) }">{{ store.detailInfo.weapon.name }}</span>
                <span class="item-meta">熟练度 {{ store.detailInfo.weapon.proficiency }}</span>
             </div>
             <div v-if="store.detailInfo.auxiliary" class="clickable-item" @click="showSecondary(store.detailInfo.auxiliary)">
                <span :style="{ color: getRarityColor(store.detailInfo.auxiliary) }">{{ store.detailInfo.auxiliary.name }}</span>
             </div>
          </div>

          <!-- 灵兽 -->
          <div class="section" v-if="store.detailInfo.spirit_animal">
             <div class="section-title">灵兽</div>
             <div class="clickable-item" @click="showSecondary(store.detailInfo.spirit_animal)">
                <span :style="{ color: getRarityColor(store.detailInfo.spirit_animal) }">{{ store.detailInfo.spirit_animal.name }}</span>
                <span class="item-meta">{{ store.detailInfo.spirit_animal.grade }}</span>
             </div>
          </div>

          <!-- 物品 -->
          <div class="section" v-if="store.detailInfo.items?.length">
             <div class="section-title">物品</div>
             <div class="items-list">
                <div 
                    v-for="item in store.detailInfo.items" 
                    :key="item.name" 
                    class="clickable-item small"
                    @click="showSecondary(item)"
                >
                   {{ item.name }} x{{ item.count }}
                </div>
             </div>
          </div>

          <!-- 关系 -->
          <div class="section" v-if="store.detailInfo.relations?.length">
             <div class="section-title">关系</div>
             <div class="relations-list">
                <div 
                    v-for="rel in store.detailInfo.relations" 
                    :key="rel.target_id" 
                    class="relation-item"
                    @click="jumpToAvatar(rel.target_id)"
                >
                   <div class="rel-name">{{ rel.name }}</div>
                   <div class="rel-desc">{{ rel.relation }}</div>
                   <div class="rel-meta">{{ rel.sect }} · {{ rel.realm }}</div>
                </div>
             </div>
          </div>
          
          <!-- 目标 -->
          <div class="section">
              <div class="section-title">长期目标</div>
              <div class="text-content">{{ store.detailInfo.long_term_objective || '无' }}</div>
          </div>
           <div class="section">
              <div class="section-title">短期目标</div>
              <div class="text-content">{{ store.detailInfo.short_term_objective || '无' }}</div>
          </div>

      </div>

      <!-- 结构化数据展示 (Region) -->
      <div v-else-if="store.detailInfo && !store.detailInfo.fallback && store.selectedTarget.type === 'region'" class="structured-content">
          <!-- Type & Desc -->
          <div class="section">
             <div class="section-title">{{ store.detailInfo.type_name }}</div>
             <div class="text-content">{{ store.detailInfo.desc }}</div>
          </div>

          <!-- Cultivate Region: Essence -->
          <div class="section" v-if="store.detailInfo.essence">
             <div class="section-title">灵气环境</div>
             <div class="text-content">
                {{ store.detailInfo.essence.type }}行灵气 · 浓度 {{ store.detailInfo.essence.density }}
             </div>
          </div>

          <!-- Normal Region: Animals -->
          <div class="section" v-if="store.detailInfo.animals?.length">
             <div class="section-title">动物分布</div>
             <div class="items-list">
                <div 
                    v-for="animal in store.detailInfo.animals" 
                    :key="animal.name" 
                    class="clickable-item small"
                    @click="showSecondary(animal)"
                >
                   <span :style="{ color: getRarityColor(animal) }">{{ animal.name }}</span>
                   <span class="item-meta">{{ animal.grade }}</span>
                </div>
             </div>
          </div>

          <!-- Normal Region: Plants -->
          <div class="section" v-if="store.detailInfo.plants?.length">
             <div class="section-title">植物分布</div>
             <div class="items-list">
                <div 
                    v-for="plant in store.detailInfo.plants" 
                    :key="plant.name" 
                    class="clickable-item small"
                    @click="showSecondary(plant)"
                >
                   <span :style="{ color: getRarityColor(plant) }">{{ plant.name }}</span>
                   <span class="item-meta">{{ plant.grade }}</span>
                </div>
             </div>
          </div>
      </div>
      
      <!-- Legacy / Fallback 展示 -->
      <ul v-else-if="store.hoverInfo.length" class="info-list">
        <li v-for="(line, index) in store.hoverInfo" :key="index">
          <template v-if="line.length">
            <span
              v-for="(segment, segIndex) in line"
              :key="segIndex"
              class="info-segment"
              :style="segment.color ? { color: segment.color } : undefined"
            >
              {{ segment.text || ' ' }}
            </span>
          </template>
          <span v-else class="info-segment">&nbsp;</span>
        </li>
      </ul>
      <div v-else class="placeholder">暂无信息</div>
    </div>

    <!-- 长期目标设定弹窗 -->
    <div v-if="showObjectiveModal" class="objective-modal">
      <div class="modal-title">设定长期目标</div>
      <textarea 
        v-model="objectiveContent" 
        placeholder="请输入该角色未来3-5年的长期目标..."
        class="objective-input"
      ></textarea>
      <div class="modal-actions">
        <button class="modal-btn confirm" @click="handleSetObjective" :disabled="!objectiveContent.trim()">确认</button>
        <button class="modal-btn cancel" @click="showObjectiveModal = false">取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.info-panel {
  position: absolute;
  top: 60px;
  right: 20px;
  width: 320px;
  max-height: calc(100vh - 40px);
  background: rgba(24, 24, 24, 0.96);
  border: 1px solid #333;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
  color: #eee;
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  overflow: visible; 
}

.panel-actions {
  display: flex;
  flex-direction: column;
  padding: 12px 14px 4px;
  gap: 6px;
  background: rgba(38, 38, 38, 0.95);
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.action-btn {
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s;
}

.action-btn.primary {
  background: #177ddc;
  color: white;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 500;
}

.action-btn.primary:hover {
  background: #1890ff;
}

.action-btn.secondary {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #aaa;
  padding: 5px 12px;
  font-size: 12px;
}

.action-btn.secondary:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.25);
  color: #ccc;
}

.info-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: rgba(38, 38, 38, 0.95);
  border-bottom: 1px solid #333;
}

.info-title {
  font-size: 16px;
  font-weight: bold;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 8px;
}

.header-subtitle {
    font-size: 12px;
    color: #888;
}

.close-btn {
  background: transparent;
  border: none;
  color: #999;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 2px 4px;
}

.close-btn:hover {
  color: #fff;
}

.close-btn-absolute {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 24px;
  height: 24px;
  background: rgba(0,0,0,0.5);
  border: 1px solid #555;
  border-radius: 4px;
  color: #ccc;
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20; /* Higher than panel-actions */
  transition: all 0.2s;
}

.close-btn-absolute:hover {
  background: rgba(255,255,255,0.2);
  color: #fff;
  border-color: #888;
}

.info-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

/* Legacy List Styles */
.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
}

.info-list li + li {
  margin-top: 6px;
}

.info-segment {
  white-space: pre-wrap;
}

/* Structured Content Styles */
.structured-content {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    background: rgba(255,255,255,0.03);
    padding: 8px;
    border-radius: 6px;
}

.stat-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.stat-item.full {
    grid-column: span 2;
}

.stat-item.clickable {
    cursor: pointer;
    transition: background 0.2s;
    border-radius: 4px;
    padding: 4px;
    margin: -4px;
    border: 1px solid transparent;
}

.stat-item.clickable:hover {
    background: rgba(255,255,255,0.08);
    border-color: rgba(255,255,255,0.1);
}

.stat-item label {
    font-size: 11px;
    color: #888;
}

.stat-item span {
    font-size: 13px;
    color: #ddd;
    font-weight: 500;
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
    letter-spacing: 0.5px;
    border-bottom: 1px solid #333;
    padding-bottom: 4px;
}

.text-content {
    font-size: 13px;
    line-height: 1.5;
    color: #ccc;
}

.tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.clickable-tag {
    font-size: 12px;
    padding: 2px 8px;
    background: rgba(255,255,255,0.05);
    border: 1px solid #444;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
}

.clickable-tag:hover {
    background: rgba(255,255,255,0.1);
    border-color: #666;
}

.clickable-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 8px;
    background: rgba(255,255,255,0.03);
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    transition: background 0.2s;
}

.clickable-item:hover {
    background: rgba(255,255,255,0.08);
}

.clickable-item.small {
    padding: 4px 8px;
    font-size: 12px;
}

.item-meta {
    font-size: 11px;
    color: #888;
}

.relations-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.relation-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 8px;
    background: rgba(0,0,0,0.2);
    border-left: 2px solid #333;
    cursor: pointer;
    transition: all 0.2s;
}

.relation-item:hover {
    background: rgba(255,255,255,0.05);
    border-left-color: #666;
}

.rel-name {
    font-size: 13px;
    font-weight: bold;
    color: #eee;
}

.rel-desc {
    font-size: 12px;
    color: #aaa;
}

.rel-meta {
    font-size: 11px;
    color: #666;
}

/* Secondary Panel Styles */
.secondary-panel {
  position: absolute;
  top: 60px;
  right: 100%;
  margin-right: 12px;
  width: 260px;
  background: rgba(32, 32, 32, 0.98);
  border: 1px solid #555;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.8);
  z-index: 90;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sec-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #444;
    padding-bottom: 8px;
}

.sec-title {
    font-size: 15px;
    font-weight: bold;
}

.close-btn-small {
    background: transparent;
    border: none;
    color: #888;
    font-size: 16px;
    cursor: pointer;
}

.close-btn-small:hover {
    color: #fff;
}

.sec-body {
    display: flex;
    flex-direction: column;
    gap: 10px;
    font-size: 13px;
    color: #ccc;
}

.tag {
    display: inline-block;
    padding: 2px 6px;
    background: #444;
    border-radius: 4px;
    font-size: 11px;
    color: #fff;
}

.sec-desc {
    line-height: 1.5;
}

.sec-effect-box {
    background: rgba(0,0,0,0.2);
    padding: 8px;
    border-radius: 4px;
    border: 1px solid #444;
}

.sec-label {
    font-size: 11px;
    color: #888;
    margin-bottom: 4px;
}

.sec-effect-text {
    color: #ffd700; /* Gold for effects */
    font-size: 12px;
    line-height: 1.4;
}

.sec-extra {
    font-size: 12px;
    border-top: 1px solid #444;
    padding-top: 8px;
}

.sub-desc {
    color: #888;
    margin-top: 2px;
}


.placeholder {
  font-size: 13px;
  color: #888;
}

.placeholder.error {
  color: #ff7875;
}

/* Modal Styles */
.objective-modal {
  position: absolute;
  top: 0;
  right: 100%;
  margin-right: 12px;
  width: 280px;
  background: rgba(32, 32, 32, 0.98);
  border: 1px solid #444;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 100;
}

.modal-title {
  font-size: 14px;
  font-weight: bold;
  color: #ddd;
}

.objective-input {
  width: 100%;
  height: 120px;
  background: #1f1f1f;
  border: 1px solid #444;
  border-radius: 4px;
  color: #eee;
  padding: 8px;
  resize: none;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.5;
  outline: none;
}

.objective-input:focus {
  border-color: #177ddc;
}

.modal-actions {
  display: flex;
  gap: 10px;
}

.modal-btn {
  flex: 1;
  padding: 6px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: opacity 0.2s;
}

.modal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-btn.confirm {
  background: #177ddc;
  color: white;
}

.modal-btn.confirm:hover:not(:disabled) {
  background: #1890ff;
}

.modal-btn.cancel {
  background: #444;
  color: #bbb;
}

.modal-btn.cancel:hover {
  background: #555;
  color: white;
}
</style>
