<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NTabs, NTabPane, NTable, NSpin } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { worldApi } from '../../../api/modules/world'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()

const loading = ref(false)
const rankings = ref<{
  heaven: any[]
  earth: any[]
  human: any[]
  sect: any[]
}>({
  heaven: [],
  earth: [],
  human: [],
  sect: []
})

const fetchRankings = async () => {
  loading.value = true
  try {
    const res = await worldApi.fetchRankings()
    rankings.value = res || { heaven: [], earth: [], human: [], sect: [] }
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
    :title="t('game.ranking.title')"
    style="width: 800px; max-height: 80vh; overflow-y: auto;"
  >
    <n-spin :show="loading">
      <n-tabs type="line" animated>
        <n-tab-pane name="heaven" :tab="t('game.ranking.heaven')">
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.ranking.rank') }}</th>
                <th>{{ t('game.ranking.name') }}</th>
                <th>{{ t('game.ranking.sect') }}</th>
                <th>{{ t('game.ranking.realm') }}</th>
                <th>{{ t('game.ranking.power') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in rankings.heaven" :key="item.id">
                <td>{{ index + 1 }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.sect }}</td>
                <td>{{ item.realm }} {{ item.stage }}</td>
                <td>{{ item.power }}</td>
              </tr>
              <tr v-if="!rankings.heaven.length">
                <td colspan="5" style="text-align: center; color: #888;">{{ t('game.ranking.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-tab-pane>

        <n-tab-pane name="earth" :tab="t('game.ranking.earth')">
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.ranking.rank') }}</th>
                <th>{{ t('game.ranking.name') }}</th>
                <th>{{ t('game.ranking.sect') }}</th>
                <th>{{ t('game.ranking.realm') }}</th>
                <th>{{ t('game.ranking.power') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in rankings.earth" :key="item.id">
                <td>{{ index + 1 }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.sect }}</td>
                <td>{{ item.realm }} {{ item.stage }}</td>
                <td>{{ item.power }}</td>
              </tr>
              <tr v-if="!rankings.earth.length">
                <td colspan="5" style="text-align: center; color: #888;">{{ t('game.ranking.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-tab-pane>

        <n-tab-pane name="human" :tab="t('game.ranking.human')">
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.ranking.rank') }}</th>
                <th>{{ t('game.ranking.name') }}</th>
                <th>{{ t('game.ranking.sect') }}</th>
                <th>{{ t('game.ranking.realm') }}</th>
                <th>{{ t('game.ranking.power') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in rankings.human" :key="item.id">
                <td>{{ index + 1 }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.sect }}</td>
                <td>{{ item.realm }} {{ item.stage }}</td>
                <td>{{ item.power }}</td>
              </tr>
              <tr v-if="!rankings.human.length">
                <td colspan="5" style="text-align: center; color: #888;">{{ t('game.ranking.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-tab-pane>

        <n-tab-pane name="sect" :tab="t('game.ranking.sect_ranking')">
          <n-table :bordered="false" :single-line="false" size="small">
            <thead>
              <tr>
                <th>{{ t('game.ranking.rank') }}</th>
                <th>{{ t('game.ranking.sect_name') }}</th>
                <th>{{ t('game.ranking.alignment') }}</th>
                <th>{{ t('game.ranking.member_count') }}</th>
                <th>{{ t('game.ranking.total_power') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in rankings.sect" :key="item.id">
                <td>{{ index + 1 }}</td>
                <td>{{ item.name }}</td>
                <td>{{ item.alignment }}</td>
                <td>{{ item.member_count }}</td>
                <td>{{ item.total_power }}</td>
              </tr>
              <tr v-if="!rankings.sect.length">
                <td colspan="5" style="text-align: center; color: #888;">{{ t('game.ranking.empty') }}</td>
              </tr>
            </tbody>
          </n-table>
        </n-tab-pane>
      </n-tabs>
    </n-spin>
  </n-modal>
</template>

<style scoped>
:deep(.n-table) {
  background-color: transparent;
}
:deep(.n-table th) {
  font-weight: bold;
}
</style>
