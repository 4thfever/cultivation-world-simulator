<script setup lang="ts">
import { NSelect, NSlider, NSwitch } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { localeRegistry } from '@/locales/registry'
import { useSettingStore } from '@/stores/setting'
import languagesIcon from '@/assets/icons/ui/lucide/languages.svg'
import volumeIcon from '@/assets/icons/ui/lucide/volume-2.svg'
import saveIcon from '@/assets/icons/ui/lucide/save.svg'

const { t } = useI18n()
const settingStore = useSettingStore()

const languageOptions = computed(() =>
  localeRegistry
    .filter((locale) => locale.enabled)
    .map((locale) => ({
      label: locale.label,
      value: locale.code,
    })),
)
</script>

<template>
  <div class="settings-panel-container">
    <div class="panel-header">
      <h3>{{ t('ui.settings') }}</h3>
    </div>

    <div class="settings-form">
      <div class="setting-item">
        <div class="setting-label-group">
          <span class="setting-icon language-badge-icon" :style="{ '--icon-url': `url(${languagesIcon})` }" aria-label="Language"></span>
          <span class="setting-label">{{ t('ui.language') }}</span>
        </div>
        <n-select
          v-model:value="settingStore.locale"
          :options="languageOptions"
          @update:value="settingStore.setLocale"
          style="width: 240px"
        />
      </div>

      <div class="setting-item">
        <div class="setting-label-group">
          <span class="setting-icon" :style="{ '--icon-url': `url(${volumeIcon})` }" aria-hidden="true"></span>
          <span class="setting-label">{{ t('ui.sound') }}</span>
        </div>

        <div class="sound-controls">
          <div class="volume-row">
            <span class="volume-label">{{ t('ui.bgm_volume') }}</span>
            <div class="slider-container">
              <n-slider
                v-model:value="settingStore.bgmVolume"
                :min="0"
                :max="1"
                :step="0.05"
                :tooltip="false"
                @update:value="settingStore.setBgmVolume"
              />
            </div>
            <span class="volume-value">{{ Math.round(settingStore.bgmVolume * 100) }}%</span>
          </div>

          <div class="volume-row">
            <span class="volume-label">{{ t('ui.sfx_volume') }}</span>
            <div class="slider-container">
              <n-slider
                v-model:value="settingStore.sfxVolume"
                :min="0"
                :max="1"
                :step="0.05"
                :tooltip="false"
                @update:value="settingStore.setSfxVolume"
              />
            </div>
            <span class="volume-value">{{ Math.round(settingStore.sfxVolume * 100) }}%</span>
          </div>
        </div>
      </div>

      <div class="setting-item">
        <div class="setting-label-group">
          <span class="setting-icon" :style="{ '--icon-url': `url(${saveIcon})` }" aria-hidden="true"></span>
          <div class="setting-description">
            <span class="setting-label">{{ t('ui.auto_save') }}</span>
            <span class="setting-subtitle">{{ t('ui.auto_save_desc') }}</span>
          </div>
        </div>
        <n-switch
          v-model:value="settingStore.isAutoSave"
          @update:value="settingStore.setAutoSave"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-panel-container {
  max-width: 600px;
  margin: 0 auto;
  padding-top: 2em;
}

.panel-header {
  margin-bottom: 3em;
  text-align: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 1.5em;
  color: #eee;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 1.25em;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 1.5em;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.setting-label-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.setting-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.9;
  color: #eee;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}

.language-badge-icon {
  opacity: 1;
}

.setting-label {
  font-size: 1.1em;
  color: #eee;
}

.setting-description {
  display: flex;
  flex-direction: column;
}

.setting-subtitle {
  font-size: 0.8em;
  color: #888;
}

.sound-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 250px;
}

.volume-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.volume-label {
  width: 80px;
  color: #aaa;
  font-size: 0.9em;
  text-align: right;
  white-space: nowrap;
}

.slider-container {
  width: 150px;
}

.volume-value {
  width: 40px;
  color: #888;
  font-size: 0.8em;
}
</style>
