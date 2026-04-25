<script setup lang="ts">
import { defineAsyncComponent, ref, watch } from 'vue'
import type { SystemMenuTab } from '@/stores/ui'
import SystemMenuShell from '@/components/SystemMenuShell.vue'

const SystemMenuStartTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuStartTab.vue'))
const SystemMenuLoadTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuLoadTab.vue'))
const SystemMenuSaveTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuSaveTab.vue'))
const SystemMenuCreateTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuCreateTab.vue'))
const SystemMenuDeleteTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuDeleteTab.vue'))
const SystemMenuLlmTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuLlmTab.vue'))
const SystemMenuSettingsTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuSettingsTab.vue'))
const SystemMenuAboutTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuAboutTab.vue'))
const SystemMenuOtherTab = defineAsyncComponent(() => import('@/components/system-menu/tabs/SystemMenuOtherTab.vue'))

const props = defineProps<{
  visible: boolean
  defaultTab?: SystemMenuTab
  gameInitialized: boolean
  closable?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'llm-ready'): void
  (e: 'return-to-main'): void
  (e: 'exit-game'): void
}>()

const activeTab = ref<SystemMenuTab>(props.defaultTab || 'load')

watch(() => props.defaultTab, (newTab) => {
  if (newTab) {
    activeTab.value = newTab
  }
})

watch(() => props.visible, (val) => {
  if (val && props.defaultTab) {
    activeTab.value = props.defaultTab
  }
})
</script>

<template>
  <SystemMenuShell
    :visible="visible"
    :active-tab="activeTab"
    :game-initialized="gameInitialized"
    :closable="closable"
    @close="emit('close')"
    @tab-change="activeTab = $event"
  >
    <SystemMenuStartTab
      v-if="activeTab === 'start'"
      :game-initialized="gameInitialized"
    />

    <SystemMenuLoadTab
      v-else-if="activeTab === 'load'"
      @close="emit('close')"
    />

    <SystemMenuSaveTab
      v-else-if="activeTab === 'save'"
      @close="emit('close')"
    />

    <SystemMenuCreateTab v-else-if="activeTab === 'create'" />
    <SystemMenuDeleteTab v-else-if="activeTab === 'delete'" />

    <SystemMenuLlmTab
      v-else-if="activeTab === 'llm'"
      @llm-ready="emit('llm-ready')"
    />

    <SystemMenuSettingsTab v-else-if="activeTab === 'settings'" />
    <SystemMenuAboutTab v-else-if="activeTab === 'about'" />

    <SystemMenuOtherTab
      v-else-if="activeTab === 'other'"
      @return-to-main="emit('return-to-main')"
      @exit-game="emit('exit-game')"
    />
  </SystemMenuShell>
</template>
