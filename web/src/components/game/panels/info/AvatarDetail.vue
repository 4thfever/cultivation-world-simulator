<script setup lang="ts">
import type { AvatarDetail } from '@/types/core';
import { formatHp } from '@/utils/formatters/number';
import StatItem from './components/StatItem.vue';
import EntityRow from './components/EntityRow.vue';
import RelationRow from './components/RelationRow.vue';
import TagList from './components/TagList.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import AvatarAdjustPanel from './components/AvatarAdjustPanel.vue';
import AvatarPortraitPanel from './components/AvatarPortraitPanel.vue';
import RoleplayPanel from './components/RoleplayPanel.vue';
import { useUiStore } from '@/stores/ui';
import { useI18n } from 'vue-i18n';
import { formatCultivationText } from '@/utils/cultivationText';
import { useAvatarDetailPanel } from '@/composables/useAvatarDetailPanel';
import brainIcon from '@/assets/icons/ui/lucide/brain.svg';
import checkIcon from '@/assets/icons/ui/lucide/check.svg';
import heartHandshakeIcon from '@/assets/icons/ui/lucide/heart-handshake.svg';
import messageCircleIcon from '@/assets/icons/ui/lucide/message-circle.svg';
import packageIcon from '@/assets/icons/ui/lucide/package.svg';
import pencilLineIcon from '@/assets/icons/ui/lucide/pencil-line.svg';
import sparklesIcon from '@/assets/icons/ui/lucide/sparkles.svg';
import triangleAlertIcon from '@/assets/icons/ui/lucide/triangle-alert.svg';

const { t, locale } = useI18n();
const props = defineProps<{
  data: AvatarDetail;
}>();

const uiStore = useUiStore();

const {
  secondaryItem,
  adjustCategory,
  showPortraitPanel,
  showObjectiveModal,
  objectiveContent,
  parsedCurrentEffects,
  portraitUrl,
  equipmentSlots,
  avatarHeaderSubtitle,
  avatarRealmText,
  formattedRanking,
  groupedRelations,
  formatGenderLabel,
  buildRelationMetaLines,
  formatRelationSub,
  showDetail,
  openAdjustPanel,
  closeAdjustPanel,
  jumpToAvatar,
  jumpToSect,
  handleSetObjective,
  handleClearObjective,
} = useAvatarDetailPanel(() => props.data, t, locale, uiStore);
</script>

<template>
  <div class="avatar-detail">
    <SecondaryPopup 
      :item="secondaryItem" 
      @close="secondaryItem = null" 
    />
    <AvatarAdjustPanel
      :avatar-id="data.id"
      :category="adjustCategory"
      :current-item="adjustCategory === 'technique' ? data.technique ?? null : adjustCategory === 'weapon' ? data.weapon ?? null : adjustCategory === 'auxiliary' ? data.auxiliary ?? null : adjustCategory === 'goldfinger' ? data.goldfinger ?? null : null"
      :current-personas="adjustCategory === 'personas' ? data.personas : []"
      @close="closeAdjustPanel"
      @updated="uiStore.refreshDetail()"
    />
    <AvatarPortraitPanel
      :avatar-id="data.id"
      :gender="data.gender"
      :race="data.race?.id"
      :realm="data.realm_id || data.realm"
      :current-pic-id="data.pic_id"
      :visible="showPortraitPanel"
      @close="showPortraitPanel = false"
      @updated="uiStore.refreshDetail()"
    />
    <div class="dead-banner" v-if="data.is_dead">
      <span class="inline-icon" :style="{ '--icon-url': `url(${triangleAlertIcon})` }" aria-hidden="true"></span>
      {{ t('game.info_panel.avatar.dead_with_reason', { reason: data.death_info?.reason || t('game.info_panel.avatar.unknown_reason') }) }}
    </div>

    <div class="content-scroll">
      <div class="avatar-header">
        <button
          class="portrait-button"
          type="button"
          :title="t('game.info_panel.avatar.portrait.entry')"
          :aria-label="t('game.info_panel.avatar.portrait.entry')"
          @click="showPortraitPanel = true"
        >
          <div class="portrait-shell">
            <img v-if="portraitUrl" class="portrait-image" :src="portraitUrl" :alt="t('game.info_panel.avatar.portrait.preview_alt')" />
            <div v-else class="portrait-fallback">{{ data.name.slice(0, 1) }}</div>
            <div class="portrait-overlay">
              <span class="portrait-overlay-text">{{ t('game.info_panel.avatar.portrait.entry') }}</span>
              <span class="portrait-edit-badge">
                <span class="portrait-edit-icon" :style="{ '--icon-url': `url(${pencilLineIcon})` }" aria-hidden="true"></span>
              </span>
            </div>
          </div>
        </button>
        <div class="avatar-header-meta">
          <div class="avatar-name">{{ data.name }}</div>
          <div class="avatar-realm">{{ avatarRealmText }}</div>
          <div class="avatar-sect">{{ avatarHeaderSubtitle }}</div>
        </div>
      </div>

      <!-- Objectives -->
      <div v-if="!data.is_dead" class="objectives-banner">
        <div class="objective-item backstory-item" v-if="data.backstory">
          <span class="label">{{ t('game.info_panel.avatar.backstory') }}</span>
          <span class="value">{{ data.backstory }}</span>
        </div>
        <div class="objective-item">
          <span class="label">{{ t('game.info_panel.avatar.long_term_objective') }}</span>
          <span class="value">{{ data.long_term_objective || t('common.none') }}</span>
        </div>
        <div class="objective-item">
          <span class="label">{{ t('game.info_panel.avatar.short_term_objective') }}</span>
          <span class="value">{{ data.short_term_objective || t('common.none') }}</span>
        </div>
      </div>

      <RoleplayPanel v-if="!data.is_dead" :avatar="data" />

      <div class="actions-bar" v-if="!data.is_dead">
        <button class="btn primary" @click="showObjectiveModal = true">{{ t('game.info_panel.avatar.set_objective') }}</button>
        <button class="btn" @click="handleClearObjective">{{ t('game.info_panel.avatar.clear_objective') }}</button>
      </div>

      <!-- Action State Banner -->
      <div v-if="!data.is_dead && data.action_state" class="action-banner">
        {{ data.action_state }}
      </div>

      <!-- Stats Grid -->
      <div class="stats-grid">
        <StatItem :label="t('game.info_panel.avatar.stats.realm')" :value="formatCultivationText(data.realm, t)" />
        <StatItem :label="t('game.info_panel.avatar.stats.age')" :value="`${data.age} / ${data.lifespan}`" />
        <StatItem 
          v-if="data.cultivation_start_age !== undefined"
          :label="t('game.info_panel.avatar.stats.awakened_age')" 
          :value="`${data.cultivation_start_age}`" 
        />
        <StatItem :label="t('game.info_panel.avatar.stats.origin')" :value="data.origin" />
        
        <StatItem :label="t('game.info_panel.avatar.stats.hp')" :value="formatHp(data.hp.cur, data.hp.max)" />
        <StatItem :label="t('game.info_panel.avatar.stats.gender')" :value="formatGenderLabel(data.gender)" />
        <StatItem
          :label="t('game.info_panel.avatar.stats.race')"
          :value="data.race?.name || t('game.info_panel.avatar.stats.unknown_race')"
          :on-click="() => showDetail(data.race)"
        />
        
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
          :label="t('game.info_panel.avatar.stats.official_rank')"
          :value="data.official_rank || t('common.none')"
          :sub-value="data.court_reputation !== undefined ? `${t('game.info_panel.avatar.stats.court_reputation')} ${data.court_reputation}` : undefined"
        />
        
        <StatItem 
          :label="t('game.info_panel.avatar.stats.root')" 
          :value="data.root" 
          :on-click="() => showDetail(data.root_detail)"
        />
        <StatItem :label="t('game.info_panel.avatar.stats.luck')" :value="data.luck" />
        <StatItem :label="t('game.info_panel.avatar.stats.magic_stone')" :value="data.magic_stone" />
        <StatItem :label="t('game.info_panel.avatar.stats.sect_contribution')" :value="data.sect_contribution ?? 0" />
        <StatItem :label="t('game.info_panel.avatar.stats.appearance')" :value="data.appearance" />
        <StatItem :label="t('game.info_panel.avatar.stats.battle_strength')" :value="data.base_battle_strength" />
        <StatItem 
          v-if="formattedRanking"
          :label="t('game.info_panel.avatar.stats.ranking')" 
          :value="formattedRanking" 
        />
        <StatItem 
          :label="t('game.info_panel.avatar.stats.emotion')" 
          :value="data.emotion.emoji" 
          :sub-value="data.emotion.name"
        />
      </div>

      <!-- Thinking -->
      <div class="section" v-if="data.thinking">
        <div class="section-title">
          <span class="section-title-icon" :style="{ '--icon-url': `url(${brainIcon})` }" aria-hidden="true"></span>
          {{ t('game.info_panel.avatar.sections.thinking') }}
        </div>
        <div class="text-content">{{ data.thinking }}</div>
      </div>

      <!-- Personas -->
      <div class="section">
        <div class="section-header">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${messageCircleIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.avatar.sections.traits') }}
          </div>
          <button class="adjust-btn" :title="t('game.info_panel.avatar.adjust.entry')" :aria-label="t('game.info_panel.avatar.adjust.entry')" @click="openAdjustPanel('personas')">
            <span class="adjust-icon" :style="{ '--icon-url': `url(${pencilLineIcon})` }" aria-hidden="true"></span>
          </button>
        </div>
        <TagList v-if="data.personas?.length" :tags="data.personas" @click="showDetail" />
        <div v-else class="empty-row">{{ t('game.info_panel.avatar.empty_short') }}</div>
      </div>

      <!-- Equipment & Sect -->
      <div class="section">
        <div class="equipment-slots plain">
          <div
            v-for="slot in equipmentSlots"
            :key="slot.category"
            class="equipment-slot-block"
          >
            <div class="section-title subsection-title">
              <span class="section-title-icon" :style="{ '--icon-url': `url(${slot.icon})` }" aria-hidden="true"></span>
              {{ slot.label }}
            </div>
            <div class="adjustable-row">
              <EntityRow
                v-if="slot.item"
                :item="slot.item"
                :meta="slot.meta"
                details-below
                @click="showDetail(slot.item)"
              />
              <div v-else class="empty-row slot-empty">{{ t('game.info_panel.avatar.empty_short') }}</div>
              <button
                class="adjust-btn inline"
                :title="t('game.info_panel.avatar.adjust.entry')"
                :aria-label="t('game.info_panel.avatar.adjust.entry')"
                @click="openAdjustPanel(slot.category)"
              >
                <span class="adjust-icon" :style="{ '--icon-url': `url(${pencilLineIcon})` }" aria-hidden="true"></span>
              </button>
            </div>
          </div>
        </div>
         <EntityRow 
          v-if="data.spirit_animal" 
          :item="data.spirit_animal" 
          details-below
          @click="showDetail(data.spirit_animal)" 
        />
      </div>

      <!-- Materials -->
      <div class="section" v-if="data.materials?.length">
        <div class="section-title">
          <span class="section-title-icon" :style="{ '--icon-url': `url(${packageIcon})` }" aria-hidden="true"></span>
          {{ t('game.info_panel.avatar.sections.materials') }}
        </div>
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
        <div class="section-title">
          <span class="section-title-icon" :style="{ '--icon-url': `url(${heartHandshakeIcon})` }" aria-hidden="true"></span>
          {{ t('game.info_panel.avatar.sections.relations') }}
        </div>
        
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
                :name="rel.name"
                :meta-lines="buildRelationMetaLines(rel)"
                :sub="formatRelationSub(rel)"
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
                :name="rel.name"
                :meta-lines="buildRelationMetaLines(rel)"
                :sub="formatRelationSub(rel)"
                :type="rel.relation_type" 
                @click="jumpToAvatar(rel.target_id)"
              />
            </template>
          </template>

          <template v-if="groupedRelations.bloodOthers.length">
            <RelationRow 
              v-for="rel in groupedRelations.bloodOthers"
              :key="rel.target_id"
              :name="rel.name"
              :meta-lines="buildRelationMetaLines(rel)"
              :sub="formatRelationSub(rel)"
              :type="rel.relation_type"
              @click="jumpToAvatar(rel.target_id)"
            />
          </template>

          <!-- Others Group -->
          <template v-if="groupedRelations.others.length">
            <RelationRow 
              v-for="rel in groupedRelations.others"
              :key="rel.target_id"
              :name="rel.name"
              :meta-lines="buildRelationMetaLines(rel)"
              :sub="formatRelationSub(rel)"
              :type="rel.relation_type"
              @click="jumpToAvatar(rel.target_id)"
            />
          </template>
        </div>
      </div>

      <!-- Effects -->
      <div class="section" v-if="parsedCurrentEffects.length">
        <div class="section-title">
          <span class="section-title-icon" :style="{ '--icon-url': `url(${sparklesIcon})` }" aria-hidden="true"></span>
          {{ t('game.info_panel.avatar.sections.current_effects') }}
        </div>
        <div class="effects-list">
          <div
            v-for="effect in parsedCurrentEffects"
            :key="effect.id"
            class="effect-row"
          >
            <div class="effect-source">{{ effect.source }}</div>
            <div class="effect-content">
              <div v-for="(segment, sIdx) in effect.segments" :key="`${effect.id}-${sIdx}`">
                {{ segment }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showObjectiveModal" class="modal-overlay">
      <div class="modal">
        <h3>{{ t('game.info_panel.avatar.modals.set_long_term') }}</h3>
        <textarea v-model="objectiveContent" :placeholder="t('game.info_panel.avatar.modals.placeholder')"></textarea>
        <div class="modal-footer">
          <button class="btn primary" @click="handleSetObjective">
            <span class="button-icon" :style="{ '--icon-url': `url(${checkIcon})` }" aria-hidden="true"></span>
            {{ t('common.confirm') }}
          </button>
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
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

.avatar-header {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: center;
  padding: 12px;
  border-radius: 10px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02)),
    rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.portrait-button {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.portrait-shell {
  position: relative;
  width: 96px;
  height: 96px;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.1), transparent 58%),
    rgba(255, 255, 255, 0.04);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease;
}

.portrait-button:hover .portrait-shell {
  border-color: rgba(23, 125, 220, 0.45);
  box-shadow: 0 0 0 1px rgba(23, 125, 220, 0.18);
  transform: translateY(-1px);
}

.portrait-image,
.portrait-fallback {
  width: 100%;
  height: 100%;
}

.portrait-image {
  object-fit: contain;
}

.portrait-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ddd;
  font-size: 32px;
  font-weight: 700;
}

.portrait-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 8px;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.04), rgba(0, 0, 0, 0.34));
  opacity: 0;
  transition: opacity 0.18s ease;
}

.portrait-button:hover .portrait-overlay {
  opacity: 1;
}

.portrait-overlay-text {
  font-size: 11px;
  color: #f2f6fb;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.34);
}

.portrait-edit-badge {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(19, 24, 31, 0.86);
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.portrait-edit-icon {
  width: 11px;
  height: 11px;
  display: block;
}

.avatar-header-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.avatar-name {
  font-size: 20px;
  line-height: 1.2;
  font-weight: 700;
  color: #f4f6f8;
}

.avatar-realm {
  font-size: 13px;
  color: #b3d7ff;
}

.avatar-sect {
  font-size: 12px;
  color: #8f98a3;
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: bold;
  color: #9f9380;
  border-bottom: 1px solid rgba(175, 148, 105, 0.32);
  padding-bottom: 4px;
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}

.equipment-slots {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.equipment-slots.plain {
  gap: 8px;
}

.equipment-slot-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subsection-title {
  margin-bottom: 2px;
  color: #a99a84;
}

.adjustable-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
}

.empty-row {
  padding: 6px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.03);
  color: #777;
  font-size: 12px;
}

.adjust-btn {
  border: none;
  background: transparent;
  color: #8a8a8a;
  font-size: 11px;
  cursor: pointer;
  padding: 1px 0 1px 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
  opacity: 0.62;
  transition: opacity 0.18s ease;
}

.adjust-btn:hover {
  opacity: 0.95;
}

.adjust-btn.inline {
  white-space: nowrap;
  align-self: center;
  margin-right: 1px;
}

.adjust-icon {
  width: 13px;
  height: 13px;
  display: block;
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

.slot-empty {
  min-height: 36px;
  display: flex;
  align-items: center;
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
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

.portrait-edit-icon,
.adjust-icon,
.section-title-icon,
.inline-icon,
.button-icon {
  display: inline-block;
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

.section-title-icon,
.inline-icon,
.button-icon {
  width: 1em;
  height: 1em;
}

.effects-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 12px;
}

.effect-row {
  display: grid;
  grid-template-columns: minmax(84px, 38%) minmax(0, 1fr);
  gap: 6px 12px;
  align-items: start;
}

.effect-source {
  color: #888;
  text-align: right;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  line-height: 1.35;
}

.effect-content {
  color: #aaddff;
  line-height: 1.4;
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

@media (max-width: 420px) {
  .effect-row {
    grid-template-columns: minmax(0, 1fr);
    gap: 4px;
  }

  .effect-source {
    text-align: left;
  }
}
</style>
