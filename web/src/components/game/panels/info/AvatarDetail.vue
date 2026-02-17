<script setup lang="ts">
import { ref, computed } from 'vue';
import type { AvatarDetail, EffectEntity } from '@/types/core';
import { RelationType } from '@/constants/relations';
import { formatHp } from '@/utils/formatters/number';
import StatItem from './components/StatItem.vue';
import EntityRow from './components/EntityRow.vue';
import RelationRow from './components/RelationRow.vue';
import TagList from './components/TagList.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import { avatarApi } from '@/api';
import { useUiStore } from '@/stores/ui';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const props = defineProps<{
  data: AvatarDetail;
}>();

const uiStore = useUiStore();
const secondaryItem = ref<EffectEntity | null>(null);
const showObjectiveModal = ref(false);
const objectiveContent = ref('');

// --- Computeds ---

const groupedRelations = computed(() => {
  const rels = props.data.relations || [];
  
  // 1. 父母 (Parents) - 对应 RelationType.TO_ME_IS_PARENT (对方是我的父母)
  const existingParents = rels.filter(r => r.relation_type === RelationType.TO_ME_IS_PARENT);
  const displayParents = [...existingParents];
  
  // 补全凡人父母占位符
  // Check genders of existing parents
  const hasFather = existingParents.some(p => p.target_gender === 'male');
  const hasMother = existingParents.some(p => p.target_gender === 'female');
  
  // 如果现有的不足2个，尝试补全
  if (existingParents.length < 2) {
    if (!hasFather) {
      displayParents.unshift({ // Father usually first
        target_id: `mortal_father_placeholder`,
        name: '', 
        relation: '', 
        relation_type: RelationType.TO_ME_IS_PARENT,
        realm: '',
        sect: '',
        is_mortal: true, 
        label_key: 'father_short'
      } as any);
    }
    
    if (!hasMother) {
      displayParents.push({
        target_id: `mortal_mother_placeholder`,
        name: '', 
        relation: '', 
        relation_type: RelationType.TO_ME_IS_PARENT,
        realm: '',
        sect: '',
        is_mortal: true, 
        label_key: 'mother_short'
      } as any);
    }
  }
  
  // 2. 子女 (Children) - 对应 RelationType.TO_ME_IS_CHILD (对方是我的子女)
  const children = rels.filter(r => r.relation_type === RelationType.TO_ME_IS_CHILD);
  
  // 3. 其他 (Others)
  const others = rels.filter(r => 
    r.relation_type !== RelationType.TO_ME_IS_PARENT && 
    r.relation_type !== RelationType.TO_ME_IS_CHILD
  );

  return {
    parents: displayParents,
    children: children,
    others: others
  };
});

// --- Actions ---

function showDetail(item: EffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item;
  }
}

function jumpToAvatar(id: string) {
  uiStore.select('avatar', id);
}

function jumpToSect(id: string) {
  uiStore.select('sect', id);
}

async function handleSetObjective() {
  if (!objectiveContent.value.trim()) return;
  try {
    await avatarApi.setLongTermObjective(props.data.id, objectiveContent.value);
    showObjectiveModal.value = false;
    objectiveContent.value = '';
    uiStore.refreshDetail();
  } catch (e) {
    console.error(e);
    alert(t('game.info_panel.avatar.modals.set_failed'));
  }
}

async function handleClearObjective() {
  if (!confirm(t('game.info_panel.avatar.modals.clear_confirm'))) return;
  try {
    await avatarApi.clearLongTermObjective(props.data.id);
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
    <div class="actions-bar" v-if="!data.is_dead">
      <button class="btn primary" @click="showObjectiveModal = true">{{ t('game.info_panel.avatar.set_objective') }}</button>
      <button class="btn" @click="handleClearObjective">{{ t('game.info_panel.avatar.clear_objective') }}</button>
    </div>
    <div class="dead-banner" v-else>
      {{ t('game.info_panel.avatar.dead_with_reason', { reason: data.death_info?.reason || t('game.info_panel.avatar.unknown_reason') }) }}
    </div>

    <div class="content-scroll">
      <!-- Objectives -->
      <div v-if="!data.is_dead" class="objectives-banner">
        <div class="objective-item">
          <span class="label">{{ t('game.info_panel.avatar.long_term_objective') }}</span>
          <span class="value">{{ data.long_term_objective || t('common.none') }}</span>
        </div>
        <div class="objective-item">
          <span class="label">{{ t('game.info_panel.avatar.short_term_objective') }}</span>
          <span class="value">{{ data.short_term_objective || t('common.none') }}</span>
        </div>
      </div>

      <!-- Action State Banner -->
      <div v-if="!data.is_dead && data.action_state" class="action-banner">
        {{ data.action_state }}
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <StatItem :label="t('game.info_panel.avatar.stats.realm')" :value="data.realm" :sub-value="data.level" />
        <StatItem :label="t('game.info_panel.avatar.stats.age')" :value="`${data.age} / ${data.lifespan}`" />
        <StatItem :label="t('game.info_panel.avatar.stats.origin')" :value="data.origin" />
        
        <StatItem :label="t('game.info_panel.avatar.stats.hp')" :value="formatHp(data.hp.cur, data.hp.max)" />
        <StatItem :label="t('game.info_panel.avatar.stats.gender')" :value="data.gender" />
        
        <StatItem 
          :label="t('game.info_panel.avatar.stats.alignment')" 
          :value="data.alignment" 
          :on-click="() => showDetail(data.alignment_detail)"
        />
        <StatItem 
          :label="t('game.info_panel.avatar.stats.sect')" 
          :value="data.sect?.name || t('game.info_panel.avatar.stats.rogue')" 
          :sub-value="data.sect?.rank"
          :on-click="data.sect ? () => jumpToSect(data.sect!.id) : (data.orthodoxy ? () => showDetail(data.orthodoxy) : undefined)"
        />
        
        <StatItem 
          :label="t('game.info_panel.avatar.stats.root')" 
          :value="data.root" 
          :on-click="() => showDetail(data.root_detail)"
        />
        <StatItem :label="t('game.info_panel.avatar.stats.magic_stone')" :value="data.magic_stone" />
        <StatItem :label="t('game.info_panel.avatar.stats.appearance')" :value="data.appearance" />
        <StatItem :label="t('game.info_panel.avatar.stats.battle_strength')" :value="data.base_battle_strength" />
        <StatItem 
          :label="t('game.info_panel.avatar.stats.emotion')" 
          :value="data.emotion.emoji" 
          :sub-value="data.emotion.name"
        />
      </div>

      <!-- Thinking -->
      <div class="section" v-if="data.thinking">
        <div class="section-title">{{ t('game.info_panel.avatar.sections.thinking') }}</div>
        <div class="text-content">{{ data.thinking }}</div>
      </div>

      <!-- Personas -->
      <div class="section" v-if="data.personas?.length">
        <div class="section-title">{{ t('game.info_panel.avatar.sections.traits') }}</div>
        <TagList :tags="data.personas" @click="showDetail" />
      </div>

      <!-- Equipment & Sect -->
      <div class="section">
        <div class="section-title">{{ t('game.info_panel.avatar.sections.techniques_equipment') }}</div>
        <EntityRow 
          v-if="data.technique" 
          :item="data.technique" 
          @click="showDetail(data.technique)" 
        />
        <EntityRow 
          v-if="data.weapon" 
          :item="data.weapon" 
          :meta="t('game.info_panel.avatar.weapon_meta', { value: data.weapon.proficiency })"
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

      <!-- Materials -->
      <div class="section" v-if="data.materials?.length">
        <div class="section-title">{{ t('game.info_panel.avatar.sections.materials') }}</div>
        <div class="list-container">
          <EntityRow 
            v-for="item in data.materials"
            :key="item.name"
            :item="item"
            :meta="`x${item.count}`"
            compact
            @click="showDetail(item)"
          />
        </div>
      </div>

      <!-- Relations (Refactored) -->
      <div class="section" v-if="data.relations?.length || groupedRelations.parents.length">
        <div class="section-title">{{ t('game.info_panel.avatar.sections.relations') }}</div>
        
        <div class="list-container">
          <!-- Parents Group -->
          <template v-if="groupedRelations.parents.length">
            <!-- Title Removed as requested -->
            <template v-for="rel in groupedRelations.parents" :key="rel.target_id">
              <!-- Mortal Parent / Placeholder -->
              <div v-if="rel.is_mortal" class="mortal-row">
                <span class="label">{{ t(`game.info_panel.avatar.${rel.label_key}`) }}</span>
                <span class="value">{{ t('game.info_panel.avatar.mortal_realm') }}</span>
              </div>
              <!-- Cultivator Parent -->
              <RelationRow 
                v-else
                :relation="rel" 
                :name="rel.name"
                :meta="t('game.info_panel.avatar.relation_meta', { owner: data.name, relation: rel.relation })"
                :sub="`${rel.sect} · ${rel.realm}`"
                :type="rel.relation_type"
                @click="jumpToAvatar(rel.target_id)"
              />
            </template>
          </template>

          <!-- Children Group -->
          <template v-if="groupedRelations.children.length">
            <template v-for="rel in groupedRelations.children" :key="rel.target_id">
              <!-- Mortal Child -->
              <div v-if="rel.is_mortal" class="mortal-row">
                <span class="label">{{ rel.name }} ({{ rel.relation }})</span>
                <span class="value">{{ t('game.info_panel.avatar.mortal_realm') }}</span>
              </div>
              <!-- Cultivator Child -->
              <RelationRow 
                v-else
                :relation="rel"
                :name="rel.name"
                :meta="t('game.info_panel.avatar.relation_meta', { owner: data.name, relation: rel.relation })"
                :sub="`${rel.sect} · ${rel.realm}`"
                :type="rel.relation_type" 
                @click="jumpToAvatar(rel.target_id)"
              />
            </template>
          </template>

          <!-- Others Group -->
          <template v-if="groupedRelations.others.length">
            <RelationRow 
              v-for="rel in groupedRelations.others"
              :key="rel.target_id"
              :relation="rel"
              :name="rel.name"
              :meta="t('game.info_panel.avatar.relation_meta', { owner: data.name, relation: rel.relation })"
              :sub="`${rel.sect} · ${rel.realm}`"
              :type="rel.relation_type"
              @click="jumpToAvatar(rel.target_id)"
            />
          </template>
        </div>
      </div>

      <!-- Effects -->
      <div class="section" v-if="data['当前效果'] && data['当前效果'] !== '无'">
        <div class="section-title">{{ t('game.info_panel.avatar.sections.current_effects') }}</div>
        <div class="effects-grid">
          <template v-for="(line, idx) in data['当前效果'].split('\n')" :key="idx">
            <div class="effect-source">{{ line.match(/^\[(.*?)\]/)?.[1] || t('ui.other') }}</div>
            <div class="effect-content">
              <div v-for="(segment, sIdx) in line.replace(/^\[.*?\]\s*/, '').split(/[;；]/)" :key="sIdx">
                {{ segment.trim() }}
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showObjectiveModal" class="modal-overlay">
      <div class="modal">
        <h3>{{ t('game.info_panel.avatar.modals.set_long_term') }}</h3>
        <textarea v-model="objectiveContent" :placeholder="t('game.info_panel.avatar.modals.placeholder')"></textarea>
        <div class="modal-footer">
          <button class="btn primary" @click="handleSetObjective">{{ t('common.confirm') }}</button>
          <button class="btn" @click="showObjectiveModal = false">{{ t('common.cancel') }}</button>
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

.dead-banner {
  background: #4a1a1a;
  color: #ffaaaa;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
  font-size: 13px;
  margin-bottom: 12px;
  border: 1px solid #7a2a2a;
}

.action-banner {
  background: rgba(23, 125, 220, 0.15);
  color: #aaddff;
  padding: 8px;
  border-radius: 4px;
  text-align: center;
  font-size: 13px;
  margin-bottom: 8px;
  border: 1px solid rgba(23, 125, 220, 0.3);
}

.objectives-banner {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 6px;
  margin-bottom: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.objective-item {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.4;
}

.objective-item .label {
  color: #888;
  white-space: nowrap;
  font-weight: bold;
}

.objective-item .value {
  color: #ccc;
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

/* Relation specific styles */
.relation-group-label {
  font-size: 11px;
  color: #555;
  margin-top: 4px;
  margin-bottom: 2px;
  padding-left: 4px;
}

.mortal-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 4px;
  font-size: 12px;
  opacity: 0.6;
  cursor: default;
}

.mortal-row .label {
  color: #aaa;
}

.mortal-row .value {
  color: #666;
  font-size: 11px;
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

.effects-grid {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 4px 12px;
  font-size: 12px;
  align-items: baseline;
}

.effect-source {
  color: #888;
  text-align: right;
  white-space: nowrap;
}

.effect-content {
  color: #aaddff;
  line-height: 1.4;
}
</style>