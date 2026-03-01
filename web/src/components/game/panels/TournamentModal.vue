<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NSpin, NEmpty } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { worldApi } from '../../../api/modules/world'
import { useWorldStore } from '../../../stores/world'
import { useUiStore } from '../../../stores/ui'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const uiStore = useUiStore()
const worldStore = useWorldStore()

const openAvatarInfo = (id: string) => {
  uiStore.select('avatar', id)
  handleShowChange(false)
}

const loading = ref(false)
const rankings = ref<{
  tournament?: any
}>({})

const fetchRankings = async () => {
  loading.value = true
  try {
    const res = await worldApi.fetchRankings()
    rankings.value = res || {}
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleShowChange = (val: boolean) => {
  emit('update:show', val)
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    fetchRankings()
  }
})
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleShowChange"
    preset="card"
    :title="t('game.ranking.tournament_title')"
    style="width: 400px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="loading">
      <div v-if="rankings.tournament">
        <div style="margin-bottom: 16px; color: #888;">
          {{ t('game.ranking.tournament_next', { years: Math.max(0, rankings.tournament.next_year - worldStore.year) }) }}
        </div>
        
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <div>
            <div style="font-weight: bold; margin-bottom: 4px;">{{ t('game.ranking.heaven_first') }}</div>
            <a v-if="rankings.tournament.heaven_first" class="clickable-text" @click="openAvatarInfo(rankings.tournament.heaven_first.id)">
              {{ rankings.tournament.heaven_first.name }}
            </a>
            <span v-else style="color: #888;">{{ t('game.ranking.empty') }}</span>
          </div>
          
          <div>
            <div style="font-weight: bold; margin-bottom: 4px;">{{ t('game.ranking.earth_first') }}</div>
            <a v-if="rankings.tournament.earth_first" class="clickable-text" @click="openAvatarInfo(rankings.tournament.earth_first.id)">
              {{ rankings.tournament.earth_first.name }}
            </a>
            <span v-else style="color: #888;">{{ t('game.ranking.empty') }}</span>
          </div>
          
          <div>
            <div style="font-weight: bold; margin-bottom: 4px;">{{ t('game.ranking.human_first') }}</div>
            <a v-if="rankings.tournament.human_first" class="clickable-text" @click="openAvatarInfo(rankings.tournament.human_first.id)">
              {{ rankings.tournament.human_first.name }}
            </a>
            <span v-else style="color: #888;">{{ t('game.ranking.empty') }}</span>
          </div>
        </div>
      </div>
      <n-empty v-else :description="t('game.ranking.empty')" style="margin: 20px 0;" />
    </n-spin>
  </n-modal>
</template>

<style scoped>
.clickable-text {
  color: #4dabf7;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.2s;
}

.clickable-text:hover {
  color: #8bc6ff;
  text-decoration: underline;
}
</style>