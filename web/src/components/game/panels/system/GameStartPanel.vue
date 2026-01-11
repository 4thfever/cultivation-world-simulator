<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NForm, NFormItem, NInputNumber, NSelect, NButton, useMessage } from 'naive-ui'
import { gameApi } from '../../../../api/game'

const props = defineProps<{
  readonly: boolean
}>()

const message = useMessage()

// 配置表单数据
const config = ref({
  init_npc_num: 12,
  sect_num: 3,
  protagonist: 'none',
  npc_awakening_rate_per_month: 0.01
})

const loading = ref(false)

// 选项
const protagonistOptions = [
  { label: '不引入主角', value: 'none' },
  { label: '随机引入主角', value: 'random' },
  { label: '全部引入主角', value: 'all' }
]

async function fetchConfig() {
  try {
    loading.value = true
    const res = await gameApi.fetchCurrentConfig()
    config.value = {
      init_npc_num: res.game.init_npc_num,
      sect_num: res.game.sect_num,
      protagonist: res.avatar.protagonist,
      npc_awakening_rate_per_month: res.game.npc_awakening_rate_per_month
    }
  } catch (e) {
    message.error('加载配置失败')
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function startGame() {
  try {
    loading.value = true
    await gameApi.startGame(config.value)
    message.success('配置已保存，正在初始化世界...')
    // 父组件会通过 polling 检测到状态变化，从而自动关闭菜单并显示 loading
  } catch (e) {
    message.error('开始游戏失败')
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
      <h3>开始游戏</h3>
      <p class="description">设定世界的初始状态。注意：游戏开始后，这些设定将无法更改。</p>
    </div>

    <n-form
      label-placement="left"
      label-width="160"
      require-mark-placement="right-hanging"
      :disabled="readonly"
    >
      <n-form-item label="初始修士数量" path="init_npc_num">
        <n-input-number v-model:value="config.init_npc_num" :min="0" :max="100" />
      </n-form-item>

      <n-form-item label="活跃宗门数量" path="sect_num">
        <n-input-number v-model:value="config.sect_num" :min="0" :max="10" />
      </n-form-item>
      <div class="tip-text" style="margin-top: -12px;">
        宗门数量建议少于角色数量的一半
      </div>

      <n-form-item label="主角引入模式" path="protagonist">
        <n-select v-model:value="config.protagonist" :options="protagonistOptions" />
      </n-form-item>
      
      <div class="tip-text" v-if="config.protagonist !== 'none'">
        <span v-if="config.protagonist === 'random'">
          随机引入：每次生成角色时，有 5% 的概率使用预设的“小说主角”模板。
        </span>
        <span v-if="config.protagonist === 'all'">
          全部引入：开局时强制生成所有预设的“小说主角”。
        </span>
      </div>

      <n-form-item label="每月新生修士概率" path="npc_awakening_rate_per_month">
        <n-input-number 
            v-model:value="config.npc_awakening_rate_per_month" 
            :min="0" 
            :max="1" 
            :step="0.001"
            :format="(val: number) => `${(val * 100).toFixed(1)}%`"
            :parse="(val: string) => parseFloat(val) / 100"
        />
      </n-form-item>

      <div class="actions" v-if="!readonly">
        <n-button type="primary" size="large" @click="startGame" :loading="loading">
          开始
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