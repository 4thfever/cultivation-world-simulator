<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { avatarApi } from '@/api';
import type { AvatarAdjustCatalogDTO, AvatarAdjustOptionDTO, CustomContentDraftDTO } from '@/types/api';
import type { EffectEntity } from '@/types/core';
import { getEntityColor, getEntityGradeTone } from '@/utils/theme';
import { logError, toErrorMessage } from '@/utils/appError';
import { useI18n } from 'vue-i18n';
import { useMessage } from 'naive-ui';
import EntityDetailCard from './EntityDetailCard.vue';
import { formatAttributeLabel, formatEntityGrade } from '@/utils/cultivationText';
import checkIcon from '@/assets/icons/ui/lucide/check.svg';
import refreshIcon from '@/assets/icons/ui/lucide/refresh-cw.svg';
import searchIcon from '@/assets/icons/ui/lucide/search.svg';
import xIcon from '@/assets/icons/ui/lucide/x.svg';

type AdjustCategory = 'technique' | 'weapon' | 'auxiliary' | 'personas' | 'goldfinger';

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
const message = useMessage();

const catalog = ref<AvatarAdjustCatalogDTO | null>(null);
const isLoading = ref(false);
const submitLoading = ref(false);
const errorText = ref('');
const searchText = ref('');
const selectedPersonaIds = ref<number[]>([]);
const customRealm = ref('CORE_FORMATION');
const customPrompt = ref('');
const customDraft = ref<CustomContentDraftDTO | null>(null);
const draftLoading = ref(false);
const saveDraftLoading = ref(false);

const categoryLabels: Record<AdjustCategory, string> = {
  technique: 'game.info_panel.avatar.adjust.categories.technique',
  weapon: 'game.info_panel.avatar.adjust.categories.weapon',
  auxiliary: 'game.info_panel.avatar.adjust.categories.auxiliary',
  personas: 'game.info_panel.avatar.adjust.categories.personas',
  goldfinger: 'game.info_panel.avatar.adjust.categories.goldfinger',
};

const singleSlotCurrentItem = computed(() => props.currentItem ?? null);

const currentPersonaSummary = computed(() => {
  return props.currentPersonas?.length ? props.currentPersonas : [];
});

const panelTitle = computed(() => {
  if (!props.category) return '';
  return t('game.info_panel.avatar.adjust.title', {
    category: t(categoryLabels[props.category]),
  });
});

const availableOptions = computed<AvatarAdjustOptionDTO[]>(() => {
  if (!catalog.value || !props.category) return [];
  switch (props.category) {
    case 'technique':
      return catalog.value.techniques;
    case 'weapon':
      return catalog.value.weapons;
    case 'auxiliary':
      return catalog.value.auxiliaries;
    case 'personas':
      return catalog.value.personas;
    case 'goldfinger':
      return catalog.value.goldfingers;
  }
});

const normalizedSearch = computed(() => searchText.value.trim().toLowerCase());
const supportsCustomGeneration = computed(() => {
  return props.category === 'technique' || props.category === 'weapon' || props.category === 'auxiliary' || props.category === 'goldfinger';
});
const needsRealmForCustomGeneration = computed(() => {
  return props.category === 'weapon' || props.category === 'auxiliary';
});

const realmOptions = computed(() => [
  { value: 'QI_REFINEMENT', label: t('realms.QI_REFINEMENT') },
  { value: 'FOUNDATION_ESTABLISHMENT', label: t('realms.FOUNDATION_ESTABLISHMENT') },
  { value: 'CORE_FORMATION', label: t('realms.CORE_FORMATION') },
  { value: 'NASCENT_SOUL', label: t('realms.NASCENT_SOUL') },
]);

const draftPreviewItem = computed<EffectEntity | null>(() => {
  if (!customDraft.value) return null;
  return {
    ...customDraft.value,
    name: customDraft.value.name || t('game.info_panel.avatar.adjust.custom.unnamed'),
    grade: customDraft.value.grade ? t(`technique_grades.${customDraft.value.grade}`) : customDraft.value.grade,
    attribute: customDraft.value.attribute ? t(`attributes.${customDraft.value.attribute}`) : customDraft.value.attribute,
    realm: customDraft.value.realm ? t(`realms.${customDraft.value.realm}`) : customDraft.value.realm,
  };
});

function getOptionGradeClass(option: Pick<EffectEntity, 'grade' | 'rarity'>): string {
  return `option-meta-${getEntityGradeTone(option.grade || option.rarity)}`;
}

const filteredOptions = computed(() => {
  const q = normalizedSearch.value;
  const rawOptions = availableOptions.value;
  const result = !q
    ? rawOptions
    : rawOptions.filter(option => {
        const haystack = `${option.name} ${option.desc || ''} ${option.effect_desc || ''} ${option.grade || ''} ${option.rarity || ''} ${option.attribute || ''}`;
        return haystack.toLowerCase().includes(q);
      });

  if (props.category === 'personas') return result;

  return [
    {
      id: '__none__',
      name: t('common.none'),
      desc: '',
    } as AvatarAdjustOptionDTO,
    ...result,
  ];
});

function syncSelectedPersonas() {
  selectedPersonaIds.value = (props.currentPersonas || [])
    .map(persona => Number(persona.id))
    .filter(id => Number.isFinite(id));
}

watch(
  () => props.currentPersonas,
  () => {
    if (props.category === 'personas') {
      syncSelectedPersonas();
    }
  },
  { immediate: true, deep: true },
);

watch(
  () => props.category,
  async category => {
    searchText.value = '';
    errorText.value = '';
    customPrompt.value = '';
    customDraft.value = null;
    if (category === 'personas') {
      syncSelectedPersonas();
    }
    if (category) {
      await ensureCatalogLoaded();
    }
  },
  { immediate: true },
);

async function ensureCatalogLoaded() {
  if (catalog.value || isLoading.value) return;
  isLoading.value = true;
  errorText.value = '';
  try {
    catalog.value = await avatarApi.fetchAvatarAdjustOptions();
  } catch (error) {
    logError('AvatarAdjustPanel.fetchAvatarAdjustOptions', error);
    errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.load_failed'));
  } finally {
    isLoading.value = false;
  }
}

async function reloadCatalog() {
  catalog.value = null;
  await ensureCatalogLoaded();
}

function isSelectedPersona(option: AvatarAdjustOptionDTO) {
  return selectedPersonaIds.value.includes(Number(option.id));
}

function togglePersona(option: AvatarAdjustOptionDTO) {
  const id = Number(option.id);
  if (!Number.isFinite(id)) return;
  if (isSelectedPersona(option)) {
    selectedPersonaIds.value = selectedPersonaIds.value.filter(item => item !== id);
    return;
  }
  selectedPersonaIds.value = [...selectedPersonaIds.value, id];
}

async function handleSingleSelect(option: AvatarAdjustOptionDTO) {
  if (!props.category || props.category === 'personas' || submitLoading.value || saveDraftLoading.value) return;

  submitLoading.value = true;
  errorText.value = '';
  try {
    await avatarApi.updateAvatarAdjustment({
      avatar_id: props.avatarId,
      category: props.category,
      target_id: option.id === '__none__' ? null : Number(option.id),
    });
    message.success(t('game.info_panel.avatar.adjust.apply_success'));
    emit('updated');
    emit('close');
  } catch (error) {
    logError('AvatarAdjustPanel.updateSingle', error);
    errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.apply_failed'));
  } finally {
    submitLoading.value = false;
  }
}

async function applyPersonas() {
  if (submitLoading.value) return;
  submitLoading.value = true;
  errorText.value = '';
  try {
    await avatarApi.updateAvatarAdjustment({
      avatar_id: props.avatarId,
      category: 'personas',
      persona_ids: selectedPersonaIds.value,
    });
    message.success(t('game.info_panel.avatar.adjust.apply_success'));
    emit('updated');
    emit('close');
  } catch (error) {
    logError('AvatarAdjustPanel.applyPersonas', error);
    errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.apply_failed'));
  } finally {
    submitLoading.value = false;
  }
}

async function generateCustomDraft() {
  if (!props.category || !supportsCustomGeneration.value || draftLoading.value) return;
  if (!customPrompt.value.trim()) {
    errorText.value = t('game.info_panel.avatar.adjust.custom.prompt_required');
    return;
  }

  draftLoading.value = true;
  errorText.value = '';
  customDraft.value = null;
  try {
    const response = await avatarApi.generateCustomContent({
      category: props.category,
      realm: needsRealmForCustomGeneration.value ? customRealm.value : undefined,
      user_prompt: customPrompt.value.trim(),
    });
    customDraft.value = response.draft;
  } catch (error) {
    logError('AvatarAdjustPanel.generateCustomDraft', error);
    errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.custom.generate_failed'));
  } finally {
    draftLoading.value = false;
  }
}

async function saveCustomDraft() {
  if (!props.category || !customDraft.value || saveDraftLoading.value) return;

  saveDraftLoading.value = true;
  errorText.value = '';
  try {
    const createResponse = await avatarApi.createCustomContent({
      category: props.category,
      draft: customDraft.value,
    });
    await reloadCatalog();
    await avatarApi.updateAvatarAdjustment({
      avatar_id: props.avatarId,
      category: props.category,
      target_id: Number(createResponse.item.id),
    });
    message.success(t('game.info_panel.avatar.adjust.custom.create_success'));
    emit('updated');
    emit('close');
  } catch (error) {
    logError('AvatarAdjustPanel.saveCustomDraft', error);
    errorText.value = toErrorMessage(error, t('game.info_panel.avatar.adjust.custom.create_failed'));
  } finally {
    saveDraftLoading.value = false;
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="category" class="adjust-panel">
      <div class="adjust-header">
        <span class="adjust-title">{{ panelTitle }}</span>
        <button class="close-btn" aria-label="Close" @click="$emit('close')">
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
