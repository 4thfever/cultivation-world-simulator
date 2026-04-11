<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useMessage } from 'naive-ui';
import { avatarApi } from '@/api';
import { useAvatarStore } from '@/stores/avatar';
import { getAvatarPortraitUrl } from '@/utils/assetUrls';
import { logError, toErrorMessage } from '@/utils/appError';
import checkIcon from '@/assets/icons/ui/lucide/check.svg';
import xIcon from '@/assets/icons/ui/lucide/x.svg';

const props = defineProps<{
  avatarId: string;
  gender: string;
  currentPicId?: number | null;
  visible: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'updated'): void;
}>();

const { t } = useI18n();
const message = useMessage();
const avatarStore = useAvatarStore();

const avatarMeta = ref<{ males: number[]; females: number[] } | null>(null);
const isLoading = ref(false);
const submitLoading = ref(false);
const errorText = ref('');
const selectedPicId = ref<number | null>(props.currentPicId ?? null);

const availableAvatars = computed(() => {
  if (!avatarMeta.value) return [];
  const normalizedGender = String(props.gender || '').toLowerCase();
  return normalizedGender === 'female' || normalizedGender === '女'
    ? avatarMeta.value.females
    : avatarMeta.value.males;
});

const previewUrl = computed(() => getAvatarPortraitUrl(props.gender, selectedPicId.value));

watch(
  () => props.currentPicId,
  value => {
    selectedPicId.value = value ?? null;
  },
  { immediate: true },
);

watch(
  () => props.visible,
  async visible => {
    errorText.value = '';
    if (!visible || avatarMeta.value || isLoading.value) return;
    isLoading.value = true;
    try {
      avatarMeta.value = await avatarApi.fetchAvatarMeta();
    } catch (error) {
      logError('AvatarPortraitPanel.fetchAvatarMeta', error);
      errorText.value = toErrorMessage(error, t('game.info_panel.avatar.portrait.load_failed'));
    } finally {
      isLoading.value = false;
    }
  },
  { immediate: true },
);

async function handleApply() {
  if (!selectedPicId.value || submitLoading.value) return;
  submitLoading.value = true;
  errorText.value = '';
  try {
    await avatarApi.updateAvatarPortrait({
      avatar_id: props.avatarId,
      pic_id: selectedPicId.value,
    });
    avatarStore.updateAvatarSummary(props.avatarId, { pic_id: selectedPicId.value });
    message.success(t('game.info_panel.avatar.portrait.apply_success'));
    emit('updated');
    emit('close');
  } catch (error) {
    logError('AvatarPortraitPanel.handleApply', error);
    errorText.value = toErrorMessage(error, t('game.info_panel.avatar.portrait.apply_failed'));
  } finally {
    submitLoading.value = false;
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="portrait-panel">
      <div class="panel-header">
        <span class="panel-title">{{ t('game.info_panel.avatar.portrait.title') }}</span>
        <button class="close-btn" aria-label="Close" @click="$emit('close')">
          <span class="icon-mask close-icon" :style="{ '--icon-url': `url(${xIcon})` }" aria-hidden="true"></span>
        </button>
      </div>

      <div class="panel-body">
        <div class="preview-block">
          <div class="block-title">{{ t('game.info_panel.avatar.portrait.current') }}</div>
          <div class="avatar-preview">
            <img v-if="previewUrl" :src="previewUrl" :alt="t('game.info_panel.avatar.portrait.preview_alt')" />
            <div v-else class="empty-preview">{{ t('game.info_panel.avatar.portrait.empty') }}</div>
          </div>
        </div>

        <div class="picker-block">
          <div class="block-title">{{ t('game.info_panel.avatar.portrait.library') }}</div>
          <div v-if="isLoading" class="state-text">{{ t('common.loading') }}</div>
          <div v-else-if="errorText" class="state-text error">{{ errorText }}</div>
          <div v-else-if="availableAvatars.length" class="avatar-grid">
            <button
              v-for="id in availableAvatars"
              :key="id"
              class="avatar-option"
              :class="{ selected: id === selectedPicId }"
              type="button"
              @click="selectedPicId = id"
            >
              <img :src="getAvatarPortraitUrl(gender, id)" :alt="`${t('game.info_panel.avatar.portrait.option_alt')} ${id}`" loading="lazy" />
            </button>
          </div>
          <div v-else class="state-text">{{ t('game.info_panel.avatar.portrait.empty_library') }}</div>
        </div>

        <div class="footer">
          <button class="action-btn primary" :disabled="!selectedPicId || submitLoading" @click="handleApply">
            <span class="icon-mask button-icon" :style="{ '--icon-url': `url(${checkIcon})` }" aria-hidden="true"></span>
            {{ submitLoading ? t('common.loading') : t('common.confirm') }}
          </button>
          <button class="action-btn" :disabled="submitLoading" @click="$emit('close')">
            {{ t('common.cancel') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.portrait-panel {
  position: fixed;
  top: 96px;
  right: calc(var(--cws-sidebar-width, 400px) + clamp(340px, 26vw, 376px) + 32px);
  width: 360px;
  background: rgba(24, 24, 24, 0.985);
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

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #444;
  padding-bottom: 8px;
}

.panel-title {
  font-size: 15px;
  font-weight: 700;
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

.button-icon {
  width: 1em;
  height: 1em;
}

.panel-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.preview-block,
.picker-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.block-title {
  font-size: 11px;
  color: #888;
  letter-spacing: 0.02em;
}

.avatar-preview {
  height: 180px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent 60%),
    rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.empty-preview {
  color: #777;
  font-size: 12px;
}

.avatar-grid {
  max-height: 276px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
  gap: 8px;
  padding-right: 2px;
}

.avatar-option {
  aspect-ratio: 1;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  overflow: hidden;
  cursor: pointer;
  padding: 4px;
  transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}

.avatar-option:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.08);
}

.avatar-option.selected {
  border-color: rgba(23, 125, 220, 0.9);
  background: rgba(23, 125, 220, 0.18);
}

.avatar-option img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.state-text {
  padding: 12px 0;
  text-align: center;
  color: #888;
  font-size: 12px;
}

.state-text.error {
  color: #ff8a8a;
}

.footer {
  display: flex;
  gap: 10px;
}

.action-btn {
  flex: 1;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.06);
  color: #ddd;
  cursor: pointer;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.action-btn.primary {
  border: none;
  background: #177ddc;
  color: #fff;
}

.action-btn:disabled {
  opacity: 0.7;
  cursor: wait;
}
</style>
