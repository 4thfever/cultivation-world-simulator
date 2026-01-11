<script setup lang="ts">
import { ref, watch } from 'vue'
import SaveLoadPanel from './game/panels/system/SaveLoadPanel.vue'
import CreateAvatarPanel from './game/panels/system/CreateAvatarPanel.vue'
import DeleteAvatarPanel from './game/panels/system/DeleteAvatarPanel.vue'
import LLMConfigPanel from './game/panels/system/LLMConfigPanel.vue'
import GameStartPanel from './game/panels/system/GameStartPanel.vue'

const props = defineProps<{
  visible: boolean
  defaultTab?: 'save' | 'load' | 'create' | 'delete' | 'llm' | 'start'
  gameInitialized: boolean
  closable?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'llm-ready'): void
}>()

const activeTab = ref<'save' | 'load' | 'create' | 'delete' | 'llm' | 'start'>(props.defaultTab || 'load')

function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
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
        <h2>系统菜单</h2>
        <!-- 只有在游戏未开始且处于 start/llm 界面时才可能无法关闭（如果是强制引导） -->
        <!-- 但为了用户体验，通常保留关闭按钮，用户如果没配置好就关闭，也只是回到 idle 状态的空界面 -->
        <button class="close-btn" @click="emit('close')" v-if="closable !== false">×</button>
      </div>
      
      <div class="menu-tabs">
        <button 
          :class="{ active: activeTab === 'start' }"
          @click="switchTab('start')"
        >
          开始游戏
        </button>
        <button 
          :class="{ active: activeTab === 'load' }"
          @click="switchTab('load')"
        >
          加载游戏
        </button>
        <button 
          :class="{ active: activeTab === 'save' }"
          @click="switchTab('save')"
          :disabled="!gameInitialized"
        >
          保存游戏
        </button>
        <button 
          :class="{ active: activeTab === 'create' }"
          @click="switchTab('create')"
          :disabled="!gameInitialized"
        >
          新建角色
        </button>
        <button 
          :class="{ active: activeTab === 'delete' }"
          @click="switchTab('delete')"
          :disabled="!gameInitialized"
        >
          删除角色
        </button>
        <button 
          :class="{ active: activeTab === 'llm' }"
          @click="switchTab('llm')"
        >
          LLM设置
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