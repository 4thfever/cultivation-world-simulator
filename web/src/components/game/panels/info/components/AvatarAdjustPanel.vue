<script setup lang="ts">
import type { EffectEntity } from '@/types/core';
import { getEntityColor } from '@/utils/theme';
import { useI18n } from 'vue-i18n';
import EntityDetailCard from './EntityDetailCard.vue';
import { formatAttributeLabel, formatEntityGrade } from '@/utils/cultivationText';
import { useAvatarAdjustmentPanel, type AdjustCategory } from '@/composables/useAvatarAdjustmentPanel';
import checkIcon from '@/assets/icons/ui/lucide/check.svg';
import refreshIcon from '@/assets/icons/ui/lucide/refresh-cw.svg';
import searchIcon from '@/assets/icons/ui/lucide/search.svg';
import xIcon from '@/assets/icons/ui/lucide/x.svg';

const props = defineProps<{
  avatarId: string;
  category: AdjustCategory | null;
  currentItem?: EffectEntity | null;
  currentPersonas?: EffectEntity[];
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'updated'): void;
}>();

const { t } = useI18n();
const {
  isLoading,
  submitLoading,
  errorText,
  searchText,
  customRealm,
  customPrompt,
  customDraft,
  draftLoading,
  saveDraftLoading,
  singleSlotCurrentItem,
  currentPersonaSummary,
  panelTitle,
  supportsCustomGeneration,
  needsRealmForCustomGeneration,
  realmOptions,
  draftPreviewItem,
  filteredOptions,
  getOptionGradeClass,
  isSelectedPersona,
  togglePersona,
  handleSingleSelect,
  applyPersonas,
  generateCustomDraft,
  saveCustomDraft,
} = useAvatarAdjustmentPanel(props, {
  onUpdated: () => emit('updated'),
  onClose: () => emit('close'),
});
</script>

<template>
  <Teleport to="body">
    <div v-if="category" class="adjust-panel">
      <div class="adjust-header">
        <span class="adjust-title">{{ panelTitle }}</span>
        <button class="close-btn" :aria-label="t('ui.close')" @click="$emit('close')">
          <span class="icon-mask close-icon" :style="{ '--icon-url': `url(${xIcon})` }" aria-hidden="true"></span>
        </button>
      </div>

      <div class="adjust-body">
        <div class="block">
          <div class="block-title">{{ t('game.info_panel.avatar.adjust.current') }}</div>

          <div v-if="category === 'personas'" class="persona-summary">
            <template v-if="currentPersonaSummary.length">
              <span
                v-for="persona in currentPersonaSummary"
                :key="persona.id || persona.name"
                class="persona-chip"
                :style="{ borderColor: getEntityColor(persona) }"
              >
                {{ persona.name }}
              </span>
            </template>
            <div v-else class="empty-text">{{ t('common.none') }}</div>
          </div>

          <EntityDetailCard
            v-else
            :item="singleSlotCurrentItem"
            :empty-label="t('common.none')"
          />
        </div>

        <div v-if="supportsCustomGeneration" class="block custom-section">
          <div class="custom-section-header">
            <div class="custom-section-title">{{ t('game.info_panel.avatar.adjust.custom.title') }}</div>
          </div>
          <select v-if="needsRealmForCustomGeneration" v-model="customRealm" class="select-input">
            <option v-for="option in realmOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <textarea
            v-model="customPrompt"
            class="prompt-input"
            :placeholder="t('game.info_panel.avatar.adjust.custom.prompt_placeholder')"
          />
          <button class="apply-btn" :disabled="draftLoading || saveDraftLoading" @click="generateCustomDraft">
            <span class="icon-mask button-icon" :style="{ '--icon-url': `url(${refreshIcon})` }" aria-hidden="true"></span>
            {{ draftLoading ? t('common.loading') : t('game.info_panel.avatar.adjust.custom.generate') }}
          </button>
          <div v-if="customDraft" class="draft-preview">
            <div class="draft-name" :style="{ color: getEntityColor(draftPreviewItem) }">
              {{ draftPreviewItem?.name }}
            </div>
            <EntityDetailCard :item="draftPreviewItem" :show-name="false" />
          </div>
          <button
            v-if="customDraft"
            class="apply-btn secondary"
            :disabled="saveDraftLoading || draftLoading"
            @click="saveCustomDraft"
          >
            <span class="icon-mask button-icon" :style="{ '--icon-url': `url(${checkIcon})` }" aria-hidden="true"></span>
            {{ saveDraftLoading ? t('common.loading') : t('game.info_panel.avatar.adjust.custom.save') }}
          </button>
        </div>

        <div class="block grow">
          <div class="block-title">{{ t('game.info_panel.avatar.adjust.select') }}</div>
          <label class="search-field">
            <span class="icon-mask search-icon" :style="{ '--icon-url': `url(${searchIcon})` }" aria-hidden="true"></span>
            <input
              v-model="searchText"
              class="search-input"
              type="text"
              :placeholder="t('game.info_panel.avatar.adjust.search_placeholder')"
            />
          </label>

          <div v-if="isLoading" class="state-text">{{ t('common.loading') }}</div>
          <div v-else-if="errorText" class="state-text error">{{ errorText }}</div>
          <div v-else class="options-list">
            <button
              v-for="option in filteredOptions"
              :key="`${category}-${option.id}-${option.name}`"
              class="option-row"
              :class="{
                selected: category === 'personas' ? isSelectedPersona(option) : false,
                disabled: submitLoading,
              }"
              :disabled="submitLoading"
              @click="category === 'personas' ? togglePersona(option) : handleSingleSelect(option)"
            >
              <div class="option-main">
                <span class="option-name" :style="{ color: getEntityColor(option) }">{{ option.name }}</span>
                <span
                  v-if="option.grade || option.rarity"
                  class="option-meta"
                  :class="getOptionGradeClass(option)"
                >
                  {{ formatEntityGrade(option.grade || option.rarity, t) }}
                </span>
                <span v-if="option.attribute" class="option-meta">{{ formatAttributeLabel(option.attribute, t) }}</span>
                <span v-if="option.is_custom" class="option-meta custom-tag">{{ t('game.info_panel.avatar.adjust.custom.tag') }}</span>
              </div>
              <div v-if="option.desc" class="option-desc">{{ option.desc }}</div>
            </button>
          </div>
        </div>

        <div v-if="category === 'personas'" class="footer">
          <button class="apply-btn" :disabled="submitLoading" @click="applyPersonas">
            <span class="icon-mask button-icon" :style="{ '--icon-url': `url(${checkIcon})` }" aria-hidden="true"></span>
            {{ submitLoading ? t('common.loading') : t('game.info_panel.avatar.adjust.apply_personas') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.adjust-panel {
  position: fixed;
  top: 96px;
  right: calc(var(--cws-sidebar-width, 400px) + clamp(340px, 26vw, 376px) + 32px);
  width: 360px;
  background: rgba(26, 26, 26, 0.985);
  border: 1px solid #555;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.8);
  z-index: 2100;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: min(360px, calc(100vw - var(--cws-sidebar-width, 400px) - clamp(340px, 26vw, 376px) - 56px));
}

.adjust-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #444;
  padding-bottom: 8px;
}

.adjust-title {
  font-size: 15px;
  font-weight: bold;
  color: #eee;
}

.close-btn {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 0 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #fff;
}

.adjust-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.custom-section {
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(72, 143, 255, 0.35);
  background:
    linear-gradient(180deg, rgba(58, 92, 150, 0.18), rgba(24, 24, 24, 0.25)),
    rgba(255, 255, 255, 0.02);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.custom-section-header {
  display: flex;
  flex-direction: column;
}

.custom-section-title {
  font-size: 13px;
  font-weight: 700;
  color: #dbe8ff;
}

.grow {
  min-height: 0;
}

.block-title {
  font-size: 11px;
  color: #888;
  letter-spacing: 0.02em;
}

.search-field {
  width: 100%;
  box-sizing: border-box;
  background: #111;
  border: 1px solid #444;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
}

.search-input {
  min-width: 0;
  flex: 1;
  background: transparent;
  border: none;
  color: #eee;
  padding: 8px 0;
  font-size: 12px;
  outline: none;
}

.select-input,
.prompt-input {
  width: 100%;
  box-sizing: border-box;
  background: #111;
  border: 1px solid #444;
  color: #eee;
  border-radius: 4px;
  font-size: 12px;
}

.select-input {
  padding: 8px 10px;
}

.prompt-input {
  min-height: 86px;
  resize: vertical;
  padding: 8px 10px;
  font-family: inherit;
}

.draft-preview {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.draft-name {
  font-size: 15px;
  font-weight: 700;
}

.options-list {
  max-height: 260px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 2px;
}

.option-row {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  cursor: pointer;
  text-align: left;
  color: #ddd;
  transition: background 0.15s, border-color 0.15s;
}

.option-row:hover:not(.disabled) {
  background: rgba(255, 255, 255, 0.08);
}

.option-row.selected {
  border-color: rgba(24, 144, 255, 0.7);
  background: rgba(24, 144, 255, 0.14);
}

.option-row.disabled {
  cursor: wait;
  opacity: 0.7;
}

.option-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.option-name {
  font-size: 13px;
  font-weight: 600;
}

.option-meta {
  font-size: 11px;
  color: #888;
}

.option-meta-default {
  color: #b9b9b9;
}

.option-meta-epic {
  color: #d7b6ff;
}

.option-meta-legendary {
  color: #fddc88;
}

.option-desc {
  font-size: 11px;
  line-height: 1.4;
  color: #999;
}

.custom-tag {
  color: #f4c96b;
}

.footer {
  display: flex;
}

.apply-btn {
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background: #177ddc;
  color: #fff;
  cursor: pointer;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.apply-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}

.apply-btn.secondary {
  background: #3f7548;
}

.state-text {
  font-size: 12px;
  color: #888;
  text-align: center;
  padding: 12px 0;
}

.state-text.error {
  color: #ff8a8a;
}

.persona-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.persona-chip {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid #444;
  border-radius: 10px;
  color: #ccc;
}

.empty-text {
  color: #888;
  font-size: 12px;
}

.icon-mask {
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

.close-icon {
  width: 18px;
  height: 18px;
}

.button-icon,
.search-icon {
  width: 1em;
  height: 1em;
}

.search-icon {
  color: #777;
}
</style>
