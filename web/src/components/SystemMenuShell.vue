<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { SystemMenuTab } from '@/stores/ui'

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

const tabs = computed((): Array<{ key: SystemMenuTab; label: string; disabled: boolean }> => ([
  { key: 'start', label: t('ui.start_game'), disabled: false },
  { key: 'load', label: t('ui.load_game'), disabled: false },
  { key: 'save', label: t('ui.save_game'), disabled: !props.gameInitialized },
  { key: 'create', label: t('ui.create_character'), disabled: !props.gameInitialized },
  { key: 'delete', label: t('ui.delete_character'), disabled: !props.gameInitialized },
  { key: 'llm', label: t('ui.llm_settings'), disabled: false },
  { key: 'settings', label: t('ui.settings'), disabled: false },
  { key: 'about', label: t('ui.about'), disabled: false },
  { key: 'other', label: t('ui.other'), disabled: false },
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
        >
          ×
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
          {{ tab.label }}
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
