<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { gameApi, type SimpleAvatarDTO } from '../../../../api/game'
import { useWorldStore } from '../../../../stores/world'
import { useMessage, NInput, NButton } from 'naive-ui'

const worldStore = useWorldStore()
const message = useMessage()
const loading = ref(false)

// --- State ---
const avatarList = ref<SimpleAvatarDTO[]>([])
const avatarSearch = ref('')

const filteredAvatars = computed(() => {
  if (!avatarSearch.value) return avatarList.value
  return avatarList.value.filter(a => a.name.includes(avatarSearch.value))
})

// --- Methods ---
async function fetchAvatarList() {
  loading.value = true
  try {
    const res = await gameApi.fetchAvatarList()
    avatarList.value = res.avatars
  } catch (e) {
    message.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

async function handleDeleteAvatar(id: string, name: string) {
  if (!confirm(`确定要删除角色 ${name} 吗？此操作不可恢复。`)) return
  
  loading.value = true
  try {
    await gameApi.deleteAvatar(id)
    message.success('删除成功')
    await Promise.all([
      fetchAvatarList(),
      worldStore.fetchState ? worldStore.fetchState() : Promise.resolve()
    ])
  } catch (e) {
    message.error('删除失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAvatarList()
})
</script>

<template>
  <div class="delete-panel">
    <div class="search-bar">
      <n-input v-model:value="avatarSearch" placeholder="搜索角色名..." />
    </div>
    <div class="avatar-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="filteredAvatars.length === 0" class="empty">未找到角色</div>
      <div 
        v-for="avatar in filteredAvatars" 
        :key="avatar.id"
        class="avatar-item"
      >
         <div class="avatar-info">
           <div class="name">{{ avatar.name }}</div>
           <div class="details">
              {{ avatar.gender }} | {{ avatar.age }}岁 | {{ avatar.realm }} | {{ avatar.sect_name }}
           </div>
         </div>
         <n-button type="error" size="small" @click="handleDeleteAvatar(avatar.id, avatar.name)">删除</n-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.delete-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.search-bar {
    margin-bottom: 15px;
}

.loading {
  text-align: center;
  color: #888;
  padding: 40px;
}

.empty {
  text-align: center;
  color: #666;
  padding: 40px;
}

.avatar-item {
  background: #222;
  border: 1px solid #333;
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: default;
  transition: background 0.2s;
}

.avatar-item:hover {
  background: #2a2a2a;
  border-color: #444;
}

.avatar-info .name {
  color: #fff;
  font-weight: bold;
  font-size: 14px;
}

.avatar-info .details {
    color: #888;
    font-size: 12px;
    margin-top: 4px;
}
</style>
