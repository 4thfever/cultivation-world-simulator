<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { NForm, NFormItem, NInputNumber, NSelect, NButton, NInput, useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { systemApi } from '../../../../api'

const { t } = useI18n()

const props = defineProps<{
  readonly: boolean
}>()

const message = useMessage()

// 配置表单数据
const config = ref({
  init_npc_num: 12,
  sect_num: 3,
  npc_awakening_rate_per_month: 0.01,
  world_history: ''
})

const loading = ref(false)

// 选项

async function fetchConfig() {
  try {
    loading.value = true
    const res = await systemApi.fetchCurrentConfig()
    config.value = {
      init_npc_num: res.game.init_npc_num,
      sect_num: res.game.sect_num,
      npc_awakening_rate_per_month: res.game.npc_awakening_rate_per_month,
      world_history: res.game.world_history || ''
    }
  } catch (e) {
    message.error(t('game_start.messages.load_failed'))
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function startGame() {
  try {
    loading.value = true
    await systemApi.startGame(config.value)
    message.success(t('game_start.messages.start_success'))
    // 父组件会通过 polling 检测到状态变化，从而自动关闭菜单并显示 loading
  } catch (e) {
    message.error(t('game_start.messages.start_failed'))
    console.error(e)
    loading.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<template>
  <div class="game-start-panel">
    <div class="panel-header">
      <h3>{{ t('game_start.title') }}</h3>
      <p class="description">{{ t('game_start.description') }}</p>
    </div>

    <n-form
      label-placement="left"
      label-width="160"
      require-mark-placement="right-hanging"
      :disabled="readonly"
    >
      <n-form-item :label="t('game_start.labels.init_npc_num')" path="init_npc_num">
        <n-input-number v-model:value="config.init_npc_num" :min="0" :max="100" />
      </n-form-item>

      <n-form-item :label="t('game_start.labels.sect_num')" path="sect_num">
        <n-input-number v-model:value="config.sect_num" :min="0" :max="10" />
      </n-form-item>
      <div class="tip-text" style="margin-top: -12px;">
        {{ t('game_start.tips.sect_num') }}
      </div>

      <n-form-item :label="t('game_start.labels.new_npc_rate')" path="npc_awakening_rate_per_month">
        <n-input-number 
            v-model:value="config.npc_awakening_rate_per_month" 
            :min="0" 
            :max="1" 
            :step="0.001"
            :format="(val: number) => `${(val * 100).toFixed(1)}%`"
            :parse="(val: string) => parseFloat(val) / 100"
        />
      </n-form-item>

      <n-form-item :label="t('game_start.labels.world_history')" path="world_history">
        <n-input
          v-model:value="config.world_history"
          type="textarea"
          :placeholder="t('game_start.placeholders.world_history')"
          :autosize="{ minRows: 3, maxRows: 6 }"
          maxlength="800"
          show-count
        />
      </n-form-item>
      <div class="tip-text" style="margin-top: -12px;">
        {{ t('game_start.tips.world_history') }}
      </div>

      <div class="actions" v-if="!readonly">
        <n-button type="primary" size="large" @click="startGame" :loading="loading">
          {{ t('game_start.actions.start') }}
        </n-button>
      </div>
    </n-form>
  </div>
</template>

<style scoped>
.game-start-panel {
  color: #eee;
  max-width: 600px;
  margin: 0 auto;
}

.panel-header {
  margin-bottom: 2em;
  text-align: center;
}

.description {
  color: #888;
  font-size: 0.9em;
}

.tip-text {
  margin-left: 160px; /* offset label width */
  margin-bottom: 24px;
  color: #aaa;
  font-size: 0.85em;
  line-height: 1.5;
}

.actions {
  display: flex;
  justify-content: center;
  margin-top: 2em;
}
</style>