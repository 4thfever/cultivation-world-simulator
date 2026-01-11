<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { gameApi, type LLMConfigDTO } from '../../../../api/game'
import { useMessage } from 'naive-ui'

const message = useMessage()
const loading = ref(false)
const testing = ref(false)
const showHelpModal = ref(false)

const config = ref<LLMConfigDTO>({
  base_url: '',
  api_key: '',
  model_name: '',
  fast_model_name: '',
  mode: 'default'
})

const modeOptions = [
  { label: '均衡 (Default)', value: 'default', desc: '自动选择模型（推荐）' },
  { label: '智能 (Normal)', value: 'normal', desc: '全用智能模型' },
  { label: '快速 (Fast)', value: 'fast', desc: '全用快速模型' }
]

const presets = [
  {
    name: '通义千问',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model_name: 'qwen-plus',
    fast_model_name: 'qwen-turbo'
  },
  {
    name: 'DeepSeek',
    base_url: 'https://api.deepseek.com',
    model_name: 'deepseek-chat',
    fast_model_name: 'deepseek-chat'
  },
  {
    name: '硅基流动',
    base_url: 'https://api.siliconflow.cn/v1',
    model_name: 'Qwen/Qwen2.5-72B-Instruct',
    fast_model_name: 'Qwen/Qwen2.5-7B-Instruct'
  },
  {
    name: 'OpenRouter',
    base_url: 'https://openrouter.ai/api/v1',
    model_name: 'anthropic/claude-3.5-sonnet',
    fast_model_name: 'google/gemini-3-flash'
  }
]

async function fetchConfig() {
  loading.value = true
  try {
    const res = await gameApi.fetchLLMConfig()
    // 确保 API Key 在前端展示为空，增加安全性提示
    config.value = { ...res, api_key: '' }
  } catch (e) {
    message.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

function applyPreset(preset: typeof presets[0]) {
  config.value.base_url = preset.base_url
  config.value.model_name = preset.model_name
  config.value.fast_model_name = preset.fast_model_name
  message.info(`已应用 ${preset.name} 预设 (请填写 API Key)`)
}

const emit = defineEmits<{
  (e: 'config-saved'): void
}>()

async function handleTestAndSave() {
  if (!config.value.api_key) {
    message.warning('请填写 API Key')
    return
  }
  if (!config.value.base_url) {
    message.warning('请填写 Base URL')
    return
  }

  testing.value = true
  try {
    // 1. 测试连接
    await gameApi.testLLMConnection(config.value)
    message.success('连接测试成功')
    
    // 2. 保存配置
    await gameApi.saveLLMConfig(config.value)
    message.success('配置已保存')
    emit('config-saved')
  } catch (e: any) {
    message.error('测试或保存失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  fetchConfig()
})
</script>

<template>
  <div class="llm-panel">
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else class="config-form">
      
      <!-- 预设按钮 -->
      <div class="section">
        <div class="section-title">快速填充</div>
        <div class="preset-buttons">
          <button 
            v-for="preset in presets" 
            :key="preset.name"
            class="preset-btn"
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </button>
        </div>
      </div>

      <!-- 核心配置 -->
      <div class="section">
        <div class="section-title">API 配置</div>
        
        <div class="form-item">
          <div class="label-row">
            <label>API Key</label>
            <button class="help-btn" @click="showHelpModal = true">什么是 API / 如何获取?</button>
          </div>
          <input 
            v-model="config.api_key" 
            type="password" 
            placeholder="在此填入你自己的 API Key (通常以 sk- 开头)"
            class="input-field"
          />
        </div>

        <div class="form-item">
          <label>Base URL</label>
          <input 
            v-model="config.base_url" 
            type="text" 
            placeholder="https://api.example.com/v1"
            class="input-field"
          />
        </div>
      </div>

      <!-- 模型配置 -->
      <div class="section">
        <div class="section-title">模型选择</div>
        
        <div class="form-item">
          <label>智能模型 (Normal)</label>
          <div class="desc">用于处理复杂逻辑、剧情生成等任务</div>
          <input 
            v-model="config.model_name" 
            type="text" 
            placeholder="例如: gpt-4, claude-3-opus, qwen-plus"
            class="input-field"
          />
        </div>

        <div class="form-item">
          <label>快速模型 (Fast)</label>
          <div class="desc">用于简单判定、频繁交互等任务</div>
          <input 
            v-model="config.fast_model_name" 
            type="text" 
            placeholder="例如: gpt-3.5-turbo, qwen-turbo"
            class="input-field"
          />
        </div>
      </div>

      <!-- 模式选择 -->
      <div class="section">
        <div class="section-title">运行模式</div>
        <div class="mode-options horizontal">
          <label 
            v-for="opt in modeOptions" 
            :key="opt.value"
            class="mode-radio"
            :class="{ active: config.mode === opt.value }"
          >
            <input 
              type="radio" 
              v-model="config.mode" 
              :value="opt.value"
              class="hidden-radio"
            />
            <div class="radio-content">
              <div class="radio-label">{{ opt.label }}</div>
              <div class="radio-desc">{{ opt.desc }}</div>
            </div>
          </label>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="action-bar">
        <button 
          class="save-btn" 
          :disabled="testing"
          @click="handleTestAndSave"
        >
          {{ testing ? '测试连接中...' : '测试连通性并保存' }}
        </button>
      </div>

    </div>

    <!-- 帮助弹窗 -->
    <div v-if="showHelpModal" class="modal-overlay" @click.self="showHelpModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>什么是 API? 新手配置指南</h3>
          <button class="close-btn" @click="showHelpModal = false">×</button>
        </div>
        
        <div class="modal-body">
          <div class="help-section">
            <h4>🌐 1. 什么是 API?</h4>
            <p>
              API (应用程序接口) 就像是一条“电话线”。本游戏本身不具备思考能力，它通过这条线连接到远端的 <strong>AI 大脑</strong> (如 Qwen 或 DeepSeek 的服务器)。当游戏进行每月结算并决定 NPC 动作时，会将相关信息通过 API 发给 AI，AI 思考后再把结果传回来。
            </p>
          </div>

          <div class="help-section">
            <h4>⚡ 2. 推荐的模型 (2025版)</h4>
            <div class="model-cards">
              <div class="card">
                <h5>Qwen-Plus / Fast</h5>
                <p>国内大厂 (阿里)，稳定且免费额度大，适合入门。</p>
              </div>
              <div class="card">
                <h5>DeepSeek V3</h5>
                <p>性价比极高，中文叙事逻辑更符合国人习惯。</p>
              </div>
              <div class="card">
                <h5>Gemini 3 Pro / Fast</h5>
                <p>Google 出品，综合性能顶尖。</p>
              </div>
            </div>
          </div>

          <div class="help-section">
            <h4>📝 3. 如何填入配置?</h4>
            <p>获得 API 后，你需要填入以下三大核心参数才能使用，通常你可以在api提供方的文档中找到这些参数怎么填：</p>
            <div class="code-block">
              <p><strong>API Base URL (接口地址):</strong> AI 的访问大门，通常由厂商提供 (如 <code>https://api.deepseek.com</code>)。</p>
              <p><strong>API Key (密钥):</strong> 你的身份凭证，就像账号密码。</p>
              <p><strong>Model Name (模型名称):</strong> 告诉服务器你想用哪颗大脑，如 <code>deepseek-chat</code> 或 <code>gemini-3-flash-preview</code>。</p>
            </div>
          </div>

          <div class="help-section">
            <h4>🔗 4. 从哪里获取 Key?</h4>
            <ul class="link-list">
               <li><a href="https://bailian.console.aliyun.com/" target="_blank">阿里云百炼 (Qwen / 最推荐)</a></li>
               <li><a href="https://platform.deepseek.com/" target="_blank">DeepSeek 开放平台 (国内推荐，便宜)</a></li>
               <li><a href="https://openrouter.ai/" target="_blank">OpenRouter (全机型聚合，推荐)</a></li>
               <li><a href="https://cloud.siliconflow.cn/" target="_blank">硅基流动 (国内聚合)</a></li>
            </ul>
          </div>

          <div class="help-section">
            <h4>🛡️ 5. 安全说明</h4>
            <p>
              您的 API Key 仅保存在您的本地电脑配置文件中 (`static/local_config.yml`)，由本地运行的游戏后端直接与模型厂商通信。本游戏 (Cultivation World Simulator) 是完全开源的程序，绝不会将您的 Key 上传至任何第三方服务器。也请注意不要把local_config.yml文件分享给任何人。
            </p>
            <p>
              使用token会产生费用，请自行评估使用成本。
            </p>
          </div>
        </div>

        <div class="modal-footer">
          <button class="confirm-btn" @click="showHelpModal = false">我明白了</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.llm-panel {
  height: 100%;
  overflow-y: auto;
  padding: 0 0.8em;
}

.loading {
  text-align: center;
  color: #888;
  padding: 3em;
}

.section {
  margin-bottom: 1.5em;
}

.section-title {
  font-size: 1em;
  font-weight: bold;
  color: #ddd;
  margin-bottom: 0.8em;
  border-left: 0.2em solid #4a9eff;
  padding-left: 0.5em;
}

.preset-buttons {
  display: flex;
  gap: 0.8em;
  flex-wrap: wrap;
}

.preset-btn {
  background: #333;
  border: 1px solid #444;
  color: #ccc;
  padding: 0.4em 0.8em;
  border-radius: 0.3em;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85em;
}

.preset-btn:hover {
  background: #444;
  border-color: #666;
  color: #fff;
}

.form-item {
  margin-bottom: 1.2em;
}

.form-item label {
  display: block;
  font-size: 0.9em;
  color: #bbb;
  margin-bottom: 0.4em;
}

.form-item .desc {
  font-size: 0.8em;
  color: #666;
  margin-bottom: 0.4em;
}

.input-field {
  width: 100%;
  background: #222;
  border: 1px solid #444;
  color: #ddd;
  padding: 0.6em 0.8em;
  border-radius: 0.3em;
  font-family: monospace;
  font-size: 0.9em;
}

.input-field:focus {
  outline: none;
  border-color: #4a9eff;
  background: #1a1a1a;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.4em;
}

.help-btn {
  background: none;
  border: 1px solid #444;
  color: #888;
  font-size: 0.8em;
  padding: 0.2em 0.6em;
  border-radius: 1em;
  cursor: pointer;
  transition: all 0.2s;
}

.help-btn:hover {
  border-color: #666;
  color: #bbb;
  background: #2a2a2a;
}

.mode-options.horizontal {
  display: flex;
  flex-direction: row;
  gap: 0.8em;
}

.mode-options.horizontal .mode-radio {
  flex: 1;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0.8em 0.4em;
}

.mode-radio {
  display: flex;
  background: #222;
  border: 1px solid #333;
  padding: 0.8em;
  border-radius: 0.3em;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-radio:hover {
  background: #2a2a2a;
}

.mode-radio.active {
  background: #1a2a3a;
  border-color: #4a9eff;
}

.hidden-radio {
  display: none;
}

.radio-content {
  flex: 1;
}

.radio-label {
  color: #ddd;
  font-size: 0.9em;
  font-weight: bold;
  margin-bottom: 0.3em;
}

.radio-desc {
  color: #777;
  font-size: 0.8em;
  line-height: 1.3;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.85);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: #0f1115;
  border: 1px solid #333;
  border-radius: 0.8em;
  width: 50em;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1.5em 3em rgba(0,0,0,0.7);
  overflow: hidden;
  font-size: 1rem; /* 重置 modal 内部字体，避免过大，或者保留继承 */
}

.modal-header {
  padding: 1.2em 1.5em;
  border-bottom: 1px solid #222;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(to bottom, #1a1c22, #0f1115);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.2em;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.5em;
}

.modal-header h3::before {
  content: "?";
  display: inline-flex;
  width: 1.4em;
  height: 1.4em;
  border: 1px solid #00e0b0;
  color: #00e0b0;
  border-radius: 50%;
  font-size: 0.9em;
  align-items: center;
  justify-content: center;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.5em;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5em;
  color: #aaa;
}

.help-section {
  margin-bottom: 2em;
}

.help-section h4 {
  color: #6da;
  font-size: 1.1em;
  margin: 0 0 0.8em 0;
}

.help-section p {
  line-height: 1.6;
  margin: 0 0 0.6em 0;
  font-size: 0.95em;
}

.model-cards {
  display: flex;
  gap: 0.8em;
  margin-top: 0.8em;
}

.card {
  flex: 1;
  background: #16181d;
  border: 1px solid #333;
  border-radius: 0.5em;
  padding: 0.8em;
}

.card h5 {
  color: #8a9eff;
  margin: 0 0 0.5em 0;
  font-size: 0.95em;
}

.card p {
  font-size: 0.85em;
  color: #777;
  margin: 0;
}

.code-block {
  background: #111;
  border: 1px solid #2a2a2a;
  border-radius: 0.5em;
  padding: 1em;
  font-family: monospace;
}

.code-block p {
  margin-bottom: 0.5em;
}

.code-block p:last-child {
  margin-bottom: 0;
}

.code-block strong {
  color: #00e0b0;
}

.code-block code {
  background: #333;
  padding: 0.1em 0.4em;
  border-radius: 0.2em;
  color: #ff79c6;
}

.link-list {
  list-style: none;
  padding: 0;
  margin: 0;
  background: #16181d;
  border: 1px solid #333;
  border-radius: 0.5em;
}

.link-list li {
  border-bottom: 1px solid #222;
}

.link-list li:last-child {
  border-bottom: none;
}

.link-list a {
  display: flex;
  justify-content: space-between;
  padding: 0.8em 1em;
  color: #ddd;
  text-decoration: none;
  font-size: 0.95em;
  transition: background 0.2s;
}

.link-list a:hover {
  background: #1f2229;
}

.link-list a::after {
  content: "↗";
  color: #666;
}

.modal-footer {
  padding: 1em 1.5em;
  border-top: 1px solid #222;
  background: #0f1115;
}

.confirm-btn {
  width: 100%;
  background: #0099cc;
  color: white;
  border: none;
  padding: 0.8em;
  border-radius: 0.4em;
  font-size: 1em;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.2s;
}

.confirm-btn:hover {
  background: #0088bb;
}

.action-bar {
  display: flex;
  justify-content: flex-end;
  padding-bottom: 1.5em;
}

.save-btn {
  background: #2a8a4a;
  color: #fff;
  border: none;
  padding: 0.7em 1.5em;
  border-radius: 0.3em;
  font-size: 0.95em;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover:not(:disabled) {
  background: #3aa85a;
}

.save-btn:disabled {
  background: #33443a;
  color: #888;
  cursor: not-allowed;
}
</style>
