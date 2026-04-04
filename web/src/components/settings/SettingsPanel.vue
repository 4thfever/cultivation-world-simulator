<script setup lang="ts">
import { NIcon, NSelect, NSlider, NSwitch } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { localeRegistry } from '@/locales/registry'
import { useSettingStore } from '@/stores/setting'

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
          <n-icon size="24" color="#eee" class="setting-icon language-badge-icon" aria-label="Language">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
              <rect x="6" y="10" width="52" height="44" rx="10" fill="none" stroke="currentColor" stroke-width="4"/>
              <path fill="currentColor" d="M15 22h18v4H15zm2 8h14v4H17zm-3 8h20v4H14z"/>
              <path fill="currentColor" d="M44 21l8 21h-4.4l-1.6-4.5h-8L36.4 42H32l8-21zm.7 12.8l-2.7-7.8l-2.8 7.8z"/>
            </svg>
          </n-icon>
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
          <n-icon size="24" color="#eee" class="setting-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="currentColor" d="M264 416.19a23.92 23.92 0 0 1-14.21-4.69l-.66-.51l-91.46-75H88a24 24 0 0 1-24-24V200a24 24 0 0 1 24-24h69.65l91.46-75l.66-.51A24 24 0 0 1 288 119.69v272.62a24 24 0 0 1-24 23.88Z"/><path fill="currentColor" d="M352 336a16 16 0 0 1-14.29-23.18c9.49-18.9 14.29-39.8 14.29-62.18s-4.8-43.28-14.29-62.18A16 16 0 1 1 366.29 174c12.78 25.4 19.24 53.48 19.24 83.35s-6.46 58-19.24 83.35A16 16 0 0 1 352 336Z"/><path fill="currentColor" d="M400 384a16 16 0 0 1-13.87-24c19.16-32.9 29.3-70.19 29.3-108s-10.14-75.1-29.3-108a16 16 0 1 1 27.74-16c21.85 37.52 33.56 80.77 33.56 124s-11.71 86.48-33.56 124A16 16 0 0 1 400 384Z"/></svg>
          </n-icon>
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
          <n-icon size="24" color="#eee" class="setting-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path fill="currentColor" d="M19 12v7H5v-7H3v7c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2v-7h-2zm-6 .67l2.59-2.58L17 11.5l-5 5l-5-5l1.41-1.41L11 12.67V3h2v9.67z"/></svg>
          </n-icon>
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
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.9;
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
