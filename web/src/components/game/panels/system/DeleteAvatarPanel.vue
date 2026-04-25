<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { NInput, NButton } from 'naive-ui'
import { useDeleteAvatarPanel } from '@/composables/useDeleteAvatarPanel'
import searchIcon from '@/assets/icons/ui/lucide/search.svg'
import trashIcon from '@/assets/icons/ui/lucide/trash-2.svg'

const { t } = useI18n()

const {
  loading,
  avatarSearch,
  filteredAvatars,
  uiKey,
  handleDeleteAvatar,
} = useDeleteAvatarPanel()
</script>

<template>
  <div class="delete-panel">
    <div class="search-bar">
      <n-input v-model:value="avatarSearch" :placeholder="t(uiKey('search_placeholder'))">
        <template #prefix>
          <span class="input-icon" :style="{ '--icon-url': `url(${searchIcon})` }" aria-hidden="true"></span>
        </template>
      </n-input>
    </div>
    <div class="avatar-list">
      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="filteredAvatars.length === 0" class="empty">{{ t(uiKey('empty')) }}</div>
      <div 
        v-for="avatar in filteredAvatars" 
        :key="avatar.id"
        class="avatar-item"
      >
         <div class="avatar-info">
           <div class="name">{{ avatar.name }}</div>
           <div class="details">
              {{ avatar.gender }} | {{ avatar.age }} {{ t(uiKey('age_unit')) }} | {{ t('realms.' + avatar.realm) }} | {{ avatar.sect_name }}
           </div>
         </div>
         <n-button type="error" size="small" @click="handleDeleteAvatar(avatar.id, avatar.name)">
           <span class="button-icon" :style="{ '--icon-url': `url(${trashIcon})` }" aria-hidden="true"></span>
           {{ t('save_load.delete') }}
         </n-button>
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

.input-icon,
.button-icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
  flex-shrink: 0;
}

.input-icon {
  color: #888;
}
</style>
