<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { SystemMenuTab } from '@/stores/ui'
import sparklesIcon from '@/assets/icons/ui/lucide/sparkles.svg'
import folderOpenIcon from '@/assets/icons/ui/lucide/folder-open.svg'
import saveIcon from '@/assets/icons/ui/lucide/save.svg'
import userPlusIcon from '@/assets/icons/ui/lucide/user-plus.svg'
import trashIcon from '@/assets/icons/ui/lucide/trash-2.svg'
import botIcon from '@/assets/icons/ui/lucide/bot.svg'
import settingsIcon from '@/assets/icons/ui/lucide/settings.svg'
import infoIcon from '@/assets/icons/ui/lucide/info.svg'
import ellipsisIcon from '@/assets/icons/ui/lucide/ellipsis.svg'
import xIcon from '@/assets/icons/ui/lucide/x.svg'

const props = defineProps<{
  visible: boolean
  activeTab: SystemMenuTab
  gameInitialized: boolean
  closable?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'tab-change', tab: SystemMenuTab): void
}>()

const { t } = useI18n()

const tabs = computed((): Array<{ key: SystemMenuTab; label: string; disabled: boolean; icon: string }> => ([
  { key: 'start', label: t('ui.start_game'), disabled: false, icon: sparklesIcon },
  { key: 'load', label: t('ui.load_game'), disabled: false, icon: folderOpenIcon },
  { key: 'save', label: t('ui.save_game'), disabled: !props.gameInitialized, icon: saveIcon },
  { key: 'create', label: t('ui.create_character'), disabled: !props.gameInitialized, icon: userPlusIcon },
  { key: 'delete', label: t('ui.delete_character'), disabled: !props.gameInitialized, icon: trashIcon },
  { key: 'llm', label: t('ui.llm_settings'), disabled: false, icon: botIcon },
  { key: 'settings', label: t('ui.settings'), disabled: false, icon: settingsIcon },
  { key: 'about', label: t('ui.about'), disabled: false, icon: infoIcon },
  { key: 'other', label: t('ui.other'), disabled: false, icon: ellipsisIcon },
]))
</script>

<template>
  <div v-if="visible" class="system-menu-overlay">
    <div class="system-menu">
      <div class="menu-header">
        <h2>{{ t('ui.system_menu_title') }}</h2>
        <button
          v-if="closable !== false"
          class="close-btn"
          @click="emit('close')"
          v-sound:cancel
          aria-label="Close"
        >
          <span class="close-icon" :style="{ '--icon-url': `url(${xIcon})` }" aria-hidden="true"></span>
        </button>
      </div>

      <div class="menu-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="{ active: activeTab === tab.key }"
          :disabled="tab.disabled"
          @click="emit('tab-change', tab.key)"
          v-sound:select
        >
          <span class="tab-inner">
            <span class="tab-icon" :style="{ '--icon-url': `url(${tab.icon})` }" aria-hidden="true"></span>
            <span class="tab-label">{{ tab.label }}</span>
          </span>
        </button>
      </div>

      <div class="menu-content">
        <slot />
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  cursor: pointer;
  padding: 0.25em 0.5em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.close-icon {
  width: 1.15em;
  height: 1.15em;
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

.tab-inner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5em;
  min-width: 0;
}

.tab-label {
  min-width: 0;
}

.tab-icon {
  width: 1em;
  height: 1em;
  flex-shrink: 0;
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
