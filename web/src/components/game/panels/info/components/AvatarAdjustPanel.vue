<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { avatarApi } from '@/api';
import type { AvatarAdjustCatalogDTO, AvatarAdjustOptionDTO } from '@/types/api';
import type { EffectEntity } from '@/types/core';
import { getEntityColor } from '@/utils/theme';
import { logError, toErrorMessage } from '@/utils/appError';
import { useI18n } from 'vue-i18n';
import { useMessage } from 'naive-ui';
import EntityDetailCard from './EntityDetailCard.vue';

type AdjustCategory = 'technique' | 'weapon' | 'auxiliary' | 'personas';

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

const categoryLabels: Record<AdjustCategory, string> = {
  technique: 'game.info_panel.avatar.adjust.categories.technique',
  weapon: 'game.info_panel.avatar.adjust.categories.weapon',
  auxiliary: 'game.info_panel.avatar.adjust.categories.auxiliary',
  personas: 'game.info_panel.avatar.adjust.categories.personas',
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
  }
});

const normalizedSearch = computed(() => searchText.value.trim().toLowerCase());

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
  if (!props.category || props.category === 'personas' || submitLoading.value) return;

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
</script>

<template>
  <Teleport to="body">
    <div v-if="category" class="adjust-panel">
      <div class="adjust-header">
        <span class="adjust-title">{{ panelTitle }}</span>
        <button class="close-btn" @click="$emit('close')">×</button>
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

        <div class="block grow">
          <div class="block-title">{{ t('game.info_panel.avatar.adjust.select') }}</div>
          <input
            v-model="searchText"
            class="search-input"
            type="text"
            :placeholder="t('game.info_panel.avatar.adjust.search_placeholder')"
          />

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
                <span v-if="option.grade || option.rarity" class="option-meta">{{ option.grade || option.rarity }}</span>
                <span v-if="option.attribute" class="option-meta">{{ option.attribute }}</span>
              </div>
              <div v-if="option.desc" class="option-desc">{{ option.desc }}</div>
            </button>
          </div>
        </div>

        <div v-if="category === 'personas'" class="footer">
          <button class="apply-btn" :disabled="submitLoading" @click="applyPersonas">
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
  right: 752px;
  width: 320px;
  background: rgba(26, 26, 26, 0.985);
  border: 1px solid #555;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 25px rgba(0, 0, 0, 0.8);
  z-index: 2100;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
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

.grow {
  min-height: 0;
}

.block-title {
  font-size: 11px;
  color: #888;
  letter-spacing: 0.02em;
}

.search-input {
  width: 100%;
  box-sizing: border-box;
  background: #111;
  border: 1px solid #444;
  color: #eee;
  padding: 8px 10px;
  border-radius: 4px;
  font-size: 12px;
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

.option-desc {
  font-size: 11px;
  line-height: 1.4;
  color: #999;
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
}

.apply-btn:disabled {
  opacity: 0.7;
  cursor: wait;
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
</style>
