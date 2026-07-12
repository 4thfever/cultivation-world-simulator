<script setup lang="ts">
import type { AvatarDetail } from '@/types/core';
import EntityRow from './components/EntityRow.vue';
import TagList from './components/TagList.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import AvatarAdjustPanel from './components/AvatarAdjustPanel.vue';
import AvatarPortraitPanel from './components/AvatarPortraitPanel.vue';
import RoleplayPanel from './components/RoleplayPanel.vue';
import AvatarDetailHeader from './avatar-detail/AvatarDetailHeader.vue';
import AvatarObjectivesBlock from './avatar-detail/AvatarObjectivesBlock.vue';
import AvatarObjectiveModal from './avatar-detail/AvatarObjectiveModal.vue';
import AvatarStatsGrid from './avatar-detail/AvatarStatsGrid.vue';
import AvatarEquipmentSection from './avatar-detail/AvatarEquipmentSection.vue';
import AvatarRelationsSection from './avatar-detail/AvatarRelationsSection.vue';
import AvatarEffectsSection from './avatar-detail/AvatarEffectsSection.vue';
import { useUiStore } from '@/stores/ui';
import { useI18n } from 'vue-i18n';
import { useAvatarDetailPanel } from '@/composables/useAvatarDetailPanel';
import brainIcon from '@/assets/icons/ui/lucide/brain.svg';
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
  currentAdjustItem,
  currentAdjustPersonas,
  avatarHeaderSubtitle,
  avatarRealmText,
  avatarCanonicalRealmText,
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
      :current-item="currentAdjustItem"
      :current-personas="currentAdjustPersonas"
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
      <AvatarDetailHeader
        :name="data.name"
        :portrait-url="portraitUrl"
        :realm-text="avatarRealmText"
        :canonical-realm-text="avatarCanonicalRealmText"
        :sect-text="avatarHeaderSubtitle"
        :portrait-title="t('game.info_panel.avatar.portrait.entry')"
        :portrait-alt="t('game.info_panel.avatar.portrait.preview_alt')"
        :canonical-realm-label="t('game.info_panel.avatar.stats.canonical_realm', { value: avatarCanonicalRealmText })"
        @edit-portrait="showPortraitPanel = true"
      />

      <AvatarObjectivesBlock
        v-if="!data.is_dead"
        :data="data"
        :none-text="t('common.none')"
        :labels="{
          backstory: t('game.info_panel.avatar.backstory'),
          fate: t('game.info_panel.avatar.fate'),
          longTermObjective: t('game.info_panel.avatar.long_term_objective'),
          shortTermObjective: t('game.info_panel.avatar.short_term_objective'),
        }"
      />

      <RoleplayPanel v-if="!data.is_dead" :avatar="data" />

      <div class="actions-bar" v-if="!data.is_dead">
        <button class="btn primary" @click="showObjectiveModal = true">{{ t('game.info_panel.avatar.set_objective') }}</button>
        <button class="btn" @click="handleClearObjective">{{ t('game.info_panel.avatar.clear_objective') }}</button>
      </div>

      <!-- Action State Banner -->
      <div v-if="!data.is_dead && data.action_state" class="action-banner">
        {{ data.action_state }}
      </div>

      <AvatarStatsGrid
        :data="data"
        :formatted-ranking="formattedRanking"
        :format-gender-label="formatGenderLabel"
        :t="t"
        @show-detail="showDetail"
        @jump-sect="jumpToSect"
      />

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

      <AvatarEquipmentSection
        :slots="equipmentSlots"
        :spirit-animal="data.spirit_animal"
        :empty-text="t('game.info_panel.avatar.empty_short')"
        :adjust-title="t('game.info_panel.avatar.adjust.entry')"
        @show-detail="showDetail"
        @adjust="openAdjustPanel"
      />

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

      <AvatarRelationsSection
        :grouped-relations="groupedRelations"
        :title="t('game.info_panel.avatar.sections.relations')"
        :mortal-realm-text="t('game.info_panel.avatar.mortal_realm')"
        :label-for="key => t(`game.info_panel.avatar.${key}`)"
        :build-relation-meta-lines="buildRelationMetaLines"
        :format-relation-sub="formatRelationSub"
        @jump-avatar="jumpToAvatar"
      >
        <template #icon>
          <span class="section-title-icon" :style="{ '--icon-url': `url(${heartHandshakeIcon})` }" aria-hidden="true"></span>
        </template>
      </AvatarRelationsSection>

      <AvatarEffectsSection
        :effects="parsedCurrentEffects"
        :title="t('game.info_panel.avatar.sections.current_effects')"
      >
        <template #icon>
          <span class="section-title-icon" :style="{ '--icon-url': `url(${sparklesIcon})` }" aria-hidden="true"></span>
        </template>
      </AvatarEffectsSection>
    </div>

    <AvatarObjectiveModal
      v-if="showObjectiveModal"
      v-model="objectiveContent"
      :title="t('game.info_panel.avatar.modals.set_long_term')"
      :placeholder="t('game.info_panel.avatar.modals.placeholder')"
      :confirm-text="t('common.confirm')"
      :cancel-text="t('common.cancel')"
      @confirm="handleSetObjective"
      @cancel="showObjectiveModal = false"
    />
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
.content-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 4px; /* Space for scrollbar */
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
/* Relation specific styles */
.relation-group-label {
  font-size: 11px;
  color: #555;
  margin-top: 4px;
  margin-bottom: 2px;
  padding-left: 4px;
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
.portrait-edit-icon,
.adjust-icon,
.section-title-icon,
.inline-icon,
.section-title-icon,
.inline-icon,
@media (max-width: 420px) {
}
</style>
