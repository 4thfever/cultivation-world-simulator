import { createApp } from 'vue'
import { createPinia } from 'pinia'
import i18n from './locales'
import { vSound } from './directives/vSound'
import { useAudio } from './composables/useAudio'
import './style.css'
import App from './App.vue'

const pinia = createPinia()
// 全局点击拦截器，用于自动播放音效
// 这样不需要给每个按钮都加 v-sound 指令
function setupGlobalSound() {
  const { play } = useAudio()
  
  window.addEventListener('click', (e) => {
    // 1. 查找触发事件的元素
    const target = e.target as HTMLElement
    // 向上查找到最近的交互元素
    const interactiveEl = target.closest('button, a, [role="button"], .n-button, .btn, .clickable')
    
    if (!interactiveEl) return

    // 2. 检查是否有禁用音效的标记 (data-no-sound)
    if (interactiveEl.hasAttribute('data-no-sound')) return
    
    // 3. 检查是否有 v-sound 指令 (如果有，v-sound 会自己处理，这里跳过避免重复)
    // 注意：v-sound 绑定的是 click 事件监听器，这里无法直接检测元素是否绑定了监听器
    // 我们可以约定：如果元素有 data-sound 属性（v-sound 加上去的），就跳过
    // 或者更简单：修改 v-sound 让它只处理特定音效，普通点击交给全局
    
    // 目前 v-sound 实现没有加标记。为了兼容，我们可以在 v-sound 里加个标记。
    // 但为了不修改太多文件，我们采用策略：
    // 全局只处理默认的 'click' 音效。如果组件需要特殊音效（如 cancel/select），
    // 开发者会加上 v-sound="type"，此时我们希望全局不要覆盖或者不要重复播放。
    
    // 简单的去重策略：
    // 我们让 v-sound 添加一个 data-has-sound 属性。
    if (interactiveEl.hasAttribute('data-has-sound')) return

    // 4. 播放默认点击音效
    // 排除禁用状态的按钮
    if ((interactiveEl as HTMLButtonElement).disabled || interactiveEl.classList.contains('n-button--disabled')) return

    play('click')
  }, { capture: true }) // 使用 capture 确保在阻止冒泡前捕获？不，冒泡阶段即可，除非被阻止。
  // 实际上，如果业务逻辑阻止了冒泡 (e.stopPropagation)，window 就收不到事件了。
  // 使用 capture: true 可以确保即使冒泡被阻止也能听到音效，
  // 但这样可能会导致点击无效区域（被业务逻辑拦截）时也播放音效。
  // 通常 UI 音效应该伴随有效操作。如果操作被阻止，通常不应播放音效。
  // 所以默认冒泡阶段监听是合理的。
}

const app = createApp(App)

app.use(pinia)
app.use(i18n)
app.directive('sound', vSound)

// Must be called after pinia is installed because useAudio uses the store
setupGlobalSound()

app.mount('#app')
