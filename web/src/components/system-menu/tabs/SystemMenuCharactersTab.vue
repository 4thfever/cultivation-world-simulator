<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NButton } from 'naive-ui'
import CreateAvatarPanel from '@/components/game/panels/system/CreateAvatarPanel.vue'
import DeleteAvatarPanel from '@/components/game/panels/system/DeleteAvatarPanel.vue'
import userPlusIcon from '@/assets/icons/ui/lucide/user-plus.svg'
import trashIcon from '@/assets/icons/ui/lucide/trash-2.svg'

const { t } = useI18n()
const mode = ref<'create' | 'delete'>('create')
</script>

<template>
  <section class="character-management">
    <header class="character-management__header">
      <h2>{{ t('ui.character_management') }}</h2>
      <div class="character-management__modes" role="tablist">
        <n-button
          :type="mode === 'create' ? 'primary' : 'default'"
          size="small"
          @click="mode = 'create'"
        >
          <span class="character-management__icon" :style="{ '--icon-url': `url(${userPlusIcon})` }" aria-hidden="true"></span>
          {{ t('ui.create_character') }}
        </n-button>
        <n-button
          :type="mode === 'delete' ? 'error' : 'default'"
          size="small"
          @click="mode = 'delete'"
        >
          <span class="character-management__icon" :style="{ '--icon-url': `url(${trashIcon})` }" aria-hidden="true"></span>
          {{ t('ui.delete_character') }}
        </n-button>
      </div>
    </header>

    <CreateAvatarPanel v-if="mode === 'create'" />
    <DeleteAvatarPanel v-else />
  </section>
</template>

<style scoped>
.character-management {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.character-management__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.character-management__header h2 {
  margin: 0;
  color: #f1f1f1;
  font-size: 18px;
  font-weight: 600;
}

.character-management__modes {
  display: inline-flex;
  gap: 8px;
}

.character-management__icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  background-color: currentColor;
  -webkit-mask: var(--icon-url) center / contain no-repeat;
  mask: var(--icon-url) center / contain no-repeat;
}
</style>
