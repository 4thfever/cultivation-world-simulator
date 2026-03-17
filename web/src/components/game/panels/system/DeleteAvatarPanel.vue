<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { avatarApi, type SimpleAvatarDTO } from '../../../../api'
import { useWorldStore } from '../../../../stores/world'
import { useMessage, NInput, NButton } from 'naive-ui'

const worldStore = useWorldStore()
const message = useMessage()
const { t, locale } = useI18n()
const loading = ref(false)

const copy = computed(() => {
  switch (locale.value) {
    case 'vi-VN':
      return {
        fetchFailed: 'Lấy danh sách nhân vật thất bại',
        deleteConfirm: 'Bạn có chắc muốn xóa nhân vật {name} không? Thao tác này không thể hoàn tác.',
        deleteSuccess: 'Xóa nhân vật thành công',
        deleteFailed: 'Xóa nhân vật thất bại',
        searchPlaceholder: 'Tìm theo tên nhân vật...',
        empty: 'Không tìm thấy nhân vật',
        ageUnit: 'tuổi',
      }
    case 'zh-CN':
      return {
        fetchFailed: '获取角色列表失败',
        deleteConfirm: '确定要删除角色 {name} 吗？此操作不可恢复。',
        deleteSuccess: '删除成功',
        deleteFailed: '删除失败',
        searchPlaceholder: '搜索角色名...',
        empty: '未找到角色',
        ageUnit: '岁',
      }
    default:
      return {
        fetchFailed: 'Failed to fetch character list',
        deleteConfirm: 'Are you sure you want to delete character {name}? This action cannot be undone.',
        deleteSuccess: 'Character deleted',
        deleteFailed: 'Failed to delete character',
        searchPlaceholder: 'Search character name...',
        empty: 'No characters found',
        ageUnit: 'years old',
      }
  }
})

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
    const res = await avatarApi.fetchAvatarList()
    avatarList.value = res.avatars
  } catch (e) {
    message.error(copy.value.fetchFailed)
  } finally {
    loading.value = false
  }
}

async function handleDeleteAvatar(id: string, name: string) {
  if (!confirm(copy.value.deleteConfirm.replace('{name}', name))) return
  
  loading.value = true
  try {
    await avatarApi.deleteAvatar(id)
    message.success(copy.value.deleteSuccess)
    await Promise.all([
      fetchAvatarList(),
      worldStore.fetchState ? worldStore.fetchState() : Promise.resolve()
    ])
  } catch (e) {
    message.error(copy.value.deleteFailed)
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
      <n-input v-model:value="avatarSearch" :placeholder="copy.searchPlaceholder" />
    </div>
    <div class="avatar-list">
      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="filteredAvatars.length === 0" class="empty">{{ copy.empty }}</div>
      <div 
        v-for="avatar in filteredAvatars" 
        :key="avatar.id"
        class="avatar-item"
      >
         <div class="avatar-info">
           <div class="name">{{ avatar.name }}</div>
           <div class="details">
              {{ avatar.gender }} | {{ avatar.age }} {{ copy.ageUnit }} | {{ t('realms.' + avatar.realm) }} | {{ avatar.sect_name }}
           </div>
         </div>
         <n-button type="error" size="small" @click="handleDeleteAvatar(avatar.id, avatar.name)">{{ t('save_load.delete') }}</n-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.delete-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
}

.search-bar {
    margin-bottom: 1em;
}

.loading {
  text-align: center;
  color: #888;
  padding: 3em;
}

.empty {
  text-align: center;
  color: #666;
  padding: 3em;
}

.avatar-item {
  background: #222;
  border: 1px solid #333;
  padding: 0.8em;
  margin-bottom: 0.8em;
  border-radius: 0.3em;
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
  font-size: 1em;
}

.avatar-info .details {
    color: #888;
    font-size: 0.85em;
    margin-top: 0.3em;
}
</style>
