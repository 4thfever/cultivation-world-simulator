import { message } from '@/utils/discreteApi'
import { logError, logWarn } from '@/utils/appError'
import i18n from '@/locales'
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

const translate = i18n.global.t

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
  const errorMessage = data.error || translate('ui.llm_connection_failed_config')
  logWarn('SocketRouter llm config required', errorMessage)
  deps.uiStore.openSystemMenu('llm', false)
  message.error(errorMessage)
}

function handleGameReinitialized(data: GameReinitializedSocketMessage, deps: SocketRouterDeps) {
  deps.worldStore.initialize().catch((e) => logError('SocketRouter reinitialize world', e))
  message.success(data.message || translate('ui.game_reinitialized'))
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

