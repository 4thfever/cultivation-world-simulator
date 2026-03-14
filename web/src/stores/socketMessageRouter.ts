import { message } from '@/utils/discreteApi'
import { logError, logWarn } from '@/utils/appError'
import type {
  TickPayloadDTO,
  ToastSocketMessage,
  LLMConfigRequiredSocketMessage,
  GameReinitializedSocketMessage,
  SocketMessageDTO,
} from '@/types/api'
import type { useUiStore } from '@/stores/ui'
import type { useWorldStore } from '@/stores/world'

interface SocketRouterDeps {
  worldStore: ReturnType<typeof useWorldStore>
  uiStore: ReturnType<typeof useUiStore>
}

function handleTickMessage(payload: TickPayloadDTO, deps: SocketRouterDeps) {
  deps.worldStore.handleTick(payload)
  if (deps.uiStore.selectedTarget) {
    deps.uiStore.refreshDetail()
  }
}

function handleToastMessage(data: ToastSocketMessage) {
  const { level, message: msg } = data
  if (level === 'error') message.error(msg)
  else if (level === 'warning') message.warning(msg)
  else if (level === 'success') message.success(msg)
  else message.info(msg)
}

function handleLlmConfigRequired(data: LLMConfigRequiredSocketMessage, deps: SocketRouterDeps) {
  const errorMessage = data.error || 'LLM 连接失败，请配置'
  logWarn('SocketRouter llm config required', errorMessage)
  deps.uiStore.openSystemMenu('llm', false)
  message.error(errorMessage)
}

function handleGameReinitialized(data: GameReinitializedSocketMessage, deps: SocketRouterDeps) {
  console.log('游戏重新初始化:', data.message)
  deps.worldStore.initialize().catch((e) => logError('SocketRouter reinitialize world', e))
  message.success(data.message || 'LLM 配置成功，游戏已重新初始化')
}

export function routeSocketMessage(data: SocketMessageDTO, deps: SocketRouterDeps) {
  switch (data.type) {
    case 'tick':
      handleTickMessage(data, deps)
      break
    case 'toast':
      handleToastMessage(data)
      break
    case 'llm_config_required':
      handleLlmConfigRequired(data, deps)
      break
    case 'game_reinitialized':
      handleGameReinitialized(data, deps)
      break
    default:
      break
  }
}

