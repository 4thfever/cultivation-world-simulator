<script setup lang="ts">
import { ref, watch } from 'vue'
import SaveLoadPanel from './game/panels/system/SaveLoadPanel.vue'
import CreateAvatarPanel from './game/panels/system/CreateAvatarPanel.vue'
import DeleteAvatarPanel from './game/panels/system/DeleteAvatarPanel.vue'
import LLMConfigPanel from './game/panels/system/LLMConfigPanel.vue'

const props = defineProps<{
  visible: boolean
  defaultTab?: 'save' | 'load' | 'create' | 'delete' | 'llm'
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const activeTab = ref<'save' | 'load' | 'create' | 'delete' | 'llm'>(props.defaultTab || 'load')

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
        <button class="close-btn" @click="emit('close')">×</button>
      </div>
      
      <div class="menu-tabs">
        <button 
          :class="{ active: activeTab === 'load' }"
          @click="switchTab('load')"
        >
          加载游戏
        </button>
        <button 
          :class="{ active: activeTab === 'save' }"
          @click="switchTab('save')"
        >
          保存游戏
        </button>
        <button 
          :class="{ active: activeTab === 'create' }"
          @click="switchTab('create')"
        >
          新建角色
        </button>
        <button 
          :class="{ active: activeTab === 'delete' }"
          @click="switchTab('delete')"
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
        <SaveLoadPanel 
          v-if="activeTab === 'save' || activeTab === 'load'" 
          :mode="activeTab === 'save' ? 'save' : 'load'"
          @close="emit('close')"
        />
        
        <CreateAvatarPanel 
          v-else-if="activeTab === 'create'" 
          @created="switchTab('create')" 
        />
        <!-- Note: @created callback could switch to list or stay, 
             currently it stays to allow creating more or just refreshes internal list -->
        
        <DeleteAvatarPanel v-else-if="activeTab === 'delete'" />
        
        <LLMConfigPanel v-else-if="activeTab === 'llm'" />
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
  width: 820px;
  height: 620px;
  border: 1px solid #333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.menu-header {
  padding: 16px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-header h2 {
  margin: 0;
  font-size: 18px;
  color: #ddd;
}

.close-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 24px;
  cursor: pointer;
}

.menu-tabs {
  display: flex;
  border-bottom: 1px solid #333;
}

.menu-tabs button {
  flex: 1;
  padding: 12px;
  background: #222;
  border: none;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
}

.menu-tabs button:hover {
  background: #2a2a2a;
}

.menu-tabs button.active {
  background: #1a1a1a;
  color: #fff;
  border-bottom: 2px solid #4a9eff;
}

.menu-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>