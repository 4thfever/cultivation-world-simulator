<script setup lang="ts">
import { onMounted } from 'vue'
import { useGameStore } from './stores/game'
import { NConfigProvider, darkTheme } from 'naive-ui'
import GameCanvas from './components/game/GameCanvas.vue'
import InfoPanel from './components/InfoPanel.vue'
import StatusBar from './components/layout/StatusBar.vue'
import EventPanel from './components/panels/EventPanel.vue'

const store = useGameStore()

onMounted(async () => {
  await store.fetchInitialState().catch((error) => {
    console.error('初始化失败', error)
  })
  store.connect()
})

function handleSelection(target: { type: 'avatar' | 'region'; id: string; name?: string }) {
  store.openInfoPanel(target)
}
</script>

<template>
  <n-config-provider :theme="darkTheme">
    <div class="app-layout">
      <StatusBar />
      <div class="main-content">
        <div class="map-container">
          <GameCanvas
            @avatarSelected="handleSelection"
            @regionSelected="handleSelection"
          />
          <InfoPanel />
        </div>
        <aside class="sidebar">
          <EventPanel />
        </aside>
      </div>
    </div>
  </n-config-provider>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background: #000;
  color: #eee;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.map-container {
  flex: 1;
  position: relative;
  background: #111;
  overflow: hidden;
}

.sidebar {
  width: 400px;
  background: #181818;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  z-index: 20;
}
</style>
