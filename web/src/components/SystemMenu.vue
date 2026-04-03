<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { NButton, NSelect, NIcon, NSwitch, NSlider } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { localeRegistry } from '../locales/registry'
import { useSettingStore } from '../stores/setting'
import SaveLoadPanel from './game/panels/system/SaveLoadPanel.vue'
import CreateAvatarPanel from './game/panels/system/CreateAvatarPanel.vue'
import DeleteAvatarPanel from './game/panels/system/DeleteAvatarPanel.vue'
import LLMConfigPanel from './game/panels/system/LLMConfigPanel.vue'
import GameStartPanel from './game/panels/system/GameStartPanel.vue'

const { t } = useI18n()
const settingStore = useSettingStore()

const props = defineProps<{
  visible: boolean
  defaultTab?: 'save' | 'load' | 'create' | 'delete' | 'llm' | 'start' | 'settings' | 'about' | 'other'
  gameInitialized: boolean
  closable?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'llm-ready'): void
  (e: 'return-to-main'): void
  (e: 'exit-game'): void
}>()

const activeTab = ref<'save' | 'load' | 'create' | 'delete' | 'llm' | 'start' | 'settings' | 'about' | 'other'>(props.defaultTab || 'load')

const languageOptions = computed(() =>
  localeRegistry
    .filter((locale) => locale.enabled)
    .map((locale) => ({
      label: locale.code === 'en-US' ? locale.label : `${locale.label} / Language`,
      value: locale.code,
    }))
)

function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
}

function openLink(url: string) {
  window.open(url, '_blank')
}

// 监听 defaultTab 变化
watch(() => props.defaultTab, (newTab) => {
  if (newTab) {
    activeTab.value = newTab
  }
})

// 当菜单打开时，如果有 defaultTab 就使用它
watch(() => props.visible, (val) => {
  if (val && props.defaultTab) {
    activeTab.value = props.defaultTab
  }
})
</script>

<template>
  <div v-if="visible" class="system-menu-overlay">
    <div class="system-menu">
      <div class="menu-header">
        <h2>{{ t('ui.system_menu_title') }}</h2>
        <!-- 只有在游戏未开始且处于 start/llm 界面时才可能无法关闭（如果是强制引导） -->
        <!-- 但为了用户体验，通常保留关闭按钮，用户如果没配置好就关闭，也只是回到 idle 状态的空界面 -->
        <button class="close-btn" @click="emit('close')" v-if="closable !== false" v-sound:cancel>×</button>
      </div>
      
      <div class="menu-tabs">
        <button 
          :class="{ active: activeTab === 'start' }"
          @click="switchTab('start')"
          v-sound:select
        >
          {{ t('ui.start_game') }}
        </button>
        <button 
          :class="{ active: activeTab === 'load' }"
          @click="switchTab('load')"
          v-sound:select
        >
          {{ t('ui.load_game') }}
        </button>
        <button 
          :class="{ active: activeTab === 'save' }"
          @click="switchTab('save')"
          :disabled="!gameInitialized"
          v-sound:select
        >
          {{ t('ui.save_game') }}
        </button>
        <button 
          :class="{ active: activeTab === 'create' }"
          @click="switchTab('create')"
          :disabled="!gameInitialized"
          v-sound:select
        >
          {{ t('ui.create_character') }}
        </button>
        <button 
          :class="{ active: activeTab === 'delete' }"
          @click="switchTab('delete')"
          :disabled="!gameInitialized"
          v-sound:select
        >
          {{ t('ui.delete_character') }}
        </button>
        <button 
          :class="{ active: activeTab === 'llm' }"
          @click="switchTab('llm')"
          v-sound:select
        >
          {{ t('ui.llm_settings') }}
        </button>
        <button 
          :class="{ active: activeTab === 'settings' }"
          @click="switchTab('settings')"
          v-sound:select
        >
          {{ t('ui.settings') }}
        </button>
        <button 
          :class="{ active: activeTab === 'about' }"
          @click="switchTab('about')"
          v-sound:select
        >
          {{ t('ui.about') }}
        </button>
        <button 
          :class="{ active: activeTab === 'other' }"
          @click="switchTab('other')"
          v-sound:select
        >
          {{ t('ui.other') }}
        </button>
      </div>

      <div class="menu-content">
        <GameStartPanel 
          v-if="activeTab === 'start'" 
          :readonly="gameInitialized"
        />

        <SaveLoadPanel 
          v-else-if="activeTab === 'save' || activeTab === 'load'" 
          :mode="activeTab === 'save' ? 'save' : 'load'"
          @close="emit('close')"
        />
        
        <CreateAvatarPanel 
          v-else-if="activeTab === 'create'" 
          @created="switchTab('create')" 
        />
        
        <DeleteAvatarPanel v-else-if="activeTab === 'delete'" />
        
        <LLMConfigPanel 
          v-else-if="activeTab === 'llm'" 
          @config-saved="emit('llm-ready')"
        />

        <div v-else-if="activeTab === 'settings'" class="settings-panel-container">
          <div class="panel-header">
            <h3>{{ t('ui.settings') }}</h3>
          </div>
          
          <div class="settings-form">
            <div class="setting-item">
              <div class="setting-label-group">
                <n-icon size="24" color="#eee" class="setting-icon language-badge-icon" aria-label="Language">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
                    <rect x="6" y="10" width="52" height="44" rx="10" fill="none" stroke="currentColor" stroke-width="4"/>
                    <path fill="currentColor" d="M19 42V22h4l7 10l7-10h4v20h-4V29l-7 9l-7-9v13z"/>
                    <path fill="currentColor" d="M46.8 44c-1.6 0-3-.3-4.2-.9c-1.1-.5-2-1.3-2.7-2.2l2.6-2.2c.5.6 1.1 1.1 1.8 1.5c.7.3 1.5.5 2.3.5c1 0 1.8-.2 2.3-.7c.5-.4.8-1 .8-1.7c0-.5-.1-.9-.4-1.2s-.8-.6-1.4-.9s-1.5-.6-2.5-.9c-1.7-.5-3-1.2-3.8-2c-.8-.8-1.2-1.9-1.2-3.3c0-1 .2-1.9.7-2.7s1.2-1.4 2.1-1.9c.9-.4 2-.7 3.3-.7c1.4 0 2.7.2 3.7.7c1 .5 1.8 1.1 2.4 1.9L50 30.6c-.4-.5-.9-.8-1.5-1.1c-.6-.3-1.2-.4-2-.4c-.8 0-1.4.2-1.9.5c-.5.4-.7.9-.7 1.5c0 .5.1.8.3 1.2c.2.3.6.6 1.2.9c.6.3 1.4.6 2.4.9c1.2.4 2.2.8 2.9 1.2c.8.5 1.4 1 1.8 1.8c.4.7.6 1.6.6 2.7c0 1.7-.6 3.1-1.8 4.1c-1.2 1-2.8 1.5-4.9 1.5Z"/>
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
                <!-- BGM Control -->
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
                
                <!-- SFX Control -->
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
                <div style="display: flex; flex-direction: column;">
                  <span class="setting-label">{{ t('ui.auto_save') }}</span>
                  <span style="font-size: 0.8em; color: #888;">{{ t('ui.auto_save_desc') }}</span>
                </div>
              </div>
              <n-switch
                v-model:value="settingStore.isAutoSave"
                @update:value="settingStore.setAutoSave"
              />
            </div>
          </div>
        </div>

        <div v-else-if="activeTab === 'about'" class="other-panel-container">
           <div class="panel-header">
             <h3>{{ t('ui.about') }}</h3>
           </div>
           
           <div class="other-actions">
              <button class="custom-action-btn" @click="openLink('https://github.com/4thfever/cultivation-world-simulator')" v-sound>
                <div class="btn-content">
                  <div class="btn-icon">⭐</div>
                  <div class="btn-text-group">
                    <span class="btn-title">{{ t('ui.about_github') }}</span>
                    <span class="btn-desc">{{ t('ui.about_github_desc') }}</span>
                  </div>
                </div>
                <div class="btn-arrow">❯</div>
              </button>
              
              <button class="custom-action-btn" @click="openLink('https://github.com/4thfever/cultivation-world-simulator/blob/main/CONTRIBUTORS.md')" v-sound>
                <div class="btn-content">
                  <div class="btn-icon">👥</div>
                  <div class="btn-text-group">
                    <span class="btn-title">{{ t('ui.about_contributors') }}</span>
                    <span class="btn-desc">{{ t('ui.about_contributors_desc') }}</span>
                  </div>
                </div>
                <div class="btn-arrow">❯</div>
              </button>
           </div>
        </div>

        <div v-else-if="activeTab === 'other'" class="other-panel-container">
           <div class="panel-header">
             <h3>{{ t('ui.other_options') }}</h3>
             <p class="description">{{ t('ui.other_options_desc') }}</p>
           </div>
           
           <div class="other-actions">
              <button class="custom-action-btn" @click="emit('return-to-main')" v-sound>
                <div class="btn-content">
                  <div class="btn-icon">🏠</div>
                  <div class="btn-text-group">
                    <span class="btn-title">{{ t('ui.return_to_main') }}</span>
                    <span class="btn-desc">{{ t('ui.return_to_main_desc') }}</span>
                  </div>
                </div>
                <div class="btn-arrow">❯</div>
              </button>
              
              <button class="custom-action-btn danger-hover" @click="emit('exit-game')" v-sound>
                <div class="btn-content">
                  <div class="btn-icon">🚪</div>
                  <div class="btn-text-group">
                    <span class="btn-title">{{ t('ui.quit_game') }}</span>
                    <span class="btn-desc">{{ t('ui.quit_game_desc') }}</span>
                  </div>
                </div>
                <div class="btn-arrow">❯</div>
              </button>
           </div>
        </div>
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

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.other-panel-container {
  max-width: 600px;
  margin: 0 auto;
  padding-top: 2em;
}

.panel-header {
  margin-bottom: 3em;
  text-align: center;
}

.panel-header h3 {
  margin: 0 0 0.5em 0;
  font-size: 1.5em;
  color: #eee;
}

.description {
  color: #888;
  font-size: 0.9em;
  margin: 0;
}

.other-actions {
  display: flex;
  flex-direction: column;
  gap: 20px; /* 间距调整 */
  width: 100%;
  padding: 0 40px;
}

/* 新的自定义按钮样式 */
.custom-action-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px 24px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  color: #eee;
  text-align: left;
  position: relative;
  overflow: hidden;
}

.custom-action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.btn-icon {
  font-size: 24px;
  opacity: 0.8;
  width: 32px;
  text-align: center;
}

.btn-text-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.btn-title {
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 1px;
}

.btn-desc {
  font-size: 12px;
  color: #888;
  transition: color 0.3s;
}

.btn-arrow {
  font-size: 18px;
  opacity: 0.3;
  transform: translateX(0);
  transition: all 0.3s ease;
}

.custom-action-btn:hover .btn-arrow {
  opacity: 0.8;
  transform: translateX(5px);
}

.custom-action-btn:hover .btn-desc {
  color: #aaa;
}

/* 危险操作（结束游戏）的微调 - 只有在 Hover 时才显露一点红色 */
.custom-action-btn.danger-hover:hover {
  border-color: rgba(255, 80, 80, 0.4);
  background: linear-gradient(90deg, rgba(255, 80, 80, 0.05), rgba(255, 255, 255, 0.05));
}

.custom-action-btn.danger-hover:hover .btn-title {
  color: #ff6666;
}

.custom-action-btn.danger-hover:hover .btn-icon {
  color: #ff6666;
}

.icon {
  font-size: 1.2em;
  margin-right: 4px;
}

.system-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.system-menu {
  background: #1a1a1a;
  width: 95vw;
  height: 90vh;
  max-width: 1920px;
  /* 动态基准字号：最小16px，正常为视口短边的2%，最大28px */
  font-size: clamp(16px, 2vmin, 28px);
  border: 1px solid #333;
  border-radius: 0.5em;
  display: flex;
  flex-direction: column;
  box-shadow: 0 0.5em 1.5em rgba(0,0,0,0.5);
}

.menu-header {
  padding: 1em;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-header h2 {
  margin: 0;
  font-size: 1.2em;
  color: #ddd;
}

.close-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 1.5em;
  cursor: pointer;
  padding: 0 0.5em;
}

.menu-tabs {
  display: flex;
  border-bottom: 1px solid #333;
}

.menu-tabs button {
  flex: 1;
  padding: 0.8em;
  background: #222;
  border: none;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1em;
}

.menu-tabs button:hover:not(:disabled) {
  background: #2a2a2a;
}

.menu-tabs button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-tabs button.active {
  background: #1a1a1a;
  color: #fff;
  border-bottom: 0.15em solid #4a9eff;
}

.menu-content {
  flex: 1;
  padding: 1.5em;
  overflow-y: auto;
}
</style>
