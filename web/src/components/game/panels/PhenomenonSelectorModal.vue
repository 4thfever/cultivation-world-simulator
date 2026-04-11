<script setup lang="ts">
import { NModal, NList, NListItem, NTag, NEmpty, useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { useWorldStore } from '@/stores/world'
import { PHENOMENON_RARITY_COLORS, STATUS_BAR_COLORS } from '@/constants/uiColors'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const store = useWorldStore()
const message = useMessage()

function getRarityColor(rarity: string) {
  return PHENOMENON_RARITY_COLORS[rarity] ?? STATUS_BAR_COLORS.neutral
}

function handleShowChange(value: boolean) {
  emit('update:show', value)
}

async function handleSelect(id: number, name: string) {
  try {
    await store.changePhenomenon(id)
    message.success(t('game.status_bar.change_success', { name }))
    emit('update:show', false)
  } catch (e) {
    message.error(t('common.error'))
  }
}
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.status_bar.selector_title')"
    style="width: 700px; max-height: 80vh; overflow-y: auto;"
  >
    <n-list hoverable clickable>
      <n-list-item v-for="p in store.phenomenaList" :key="p.id" @click="handleSelect(p.id, p.name)" v-sound:select>
        <div class="list-item-content">
          <div class="item-left">
            <div class="item-name" :style="{ color: getRarityColor(p.rarity) }">
              {{ p.name }}
              <n-tag size="small" :bordered="false" :color="{ color: 'rgba(255,255,255,0.1)', textColor: getRarityColor(p.rarity) }">
                {{ p.rarity }}
              </n-tag>
            </div>
            <div class="item-desc">{{ p.desc }}</div>
          </div>
          <div class="item-right">
            <div class="item-effect" v-if="p.effect_desc">{{ p.effect_desc }}</div>
          </div>
        </div>
      </n-list-item>
      <n-empty v-if="store.phenomenaList.length === 0" :description="t('game.status_bar.empty_data')" />
    </n-list>
  </n-modal>
</template>

<style scoped>
.list-item-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

.item-name {
  font-weight: bold;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-desc {
  color: #aeb4bc;
  font-size: 13px;
}

.item-effect {
  font-size: 12px;
  color: #d8a14a;
  background: rgba(216, 161, 74, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 4px;
}
</style>
