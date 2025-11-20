import type { TickPayload } from '../types/game'

export interface GatewayHandlers {
  onTick?: (payload: TickPayload) => void
  onStatusChange?: (connected: boolean) => void
  onError?: (error: unknown) => void
}

export interface GatewayOptions {
  reconnect?: boolean
  url?: string
  baseDelay?: number
  maxDelay?: number
}

export function createGameGateway(
  handlers: GatewayHandlers,
  options: GatewayOptions = {}
) {
  const reconnectEnabled = options.reconnect !== false
  const baseDelay = options.baseDelay ?? 1000
  const maxDelay = options.maxDelay ?? 8000

  let ws: WebSocket | null = null
  let reconnectTimer: number | null = null
  let reconnectAttempts = 0
  let manuallyClosed = false

  function getUrl() {
    if (options.url) return options.url
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}/ws`
  }

  function clearReconnectTimer() {
    if (reconnectTimer != null) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  function cleanupSocket() {
    if (!ws) return
    ws.onopen = null
    ws.onmessage = null
    ws.onerror = null
    ws.onclose = null
    ws = null
  }

  function scheduleReconnect() {
    if (!reconnectEnabled || manuallyClosed) return
    clearReconnectTimer()
    const delay = Math.min(maxDelay, baseDelay * 2 ** reconnectAttempts)
    reconnectAttempts += 1
    reconnectTimer = window.setTimeout(() => {
      connect()
    }, delay)
  }

  function handleMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data)
      if (data?.type === 'tick') {
        handlers.onTick?.(data as TickPayload)
      }
    } catch (error) {
      handlers.onError?.(error)
    }
  }

  function handleOpen() {
    reconnectAttempts = 0
    handlers.onStatusChange?.(true)
  }

  function handleClose() {
    handlers.onStatusChange?.(false)
    cleanupSocket()
    scheduleReconnect()
  }

  function handleError(error: Event) {
    handlers.onError?.(error)
  }

  function connect() {
    manuallyClosed = false
    clearReconnectTimer()
    cleanupSocket()

    try {
      ws = new WebSocket(getUrl())
      ws.onopen = handleOpen
      ws.onmessage = handleMessage
      ws.onerror = handleError
      ws.onclose = handleClose
    } catch (error) {
      handlers.onError?.(error)
      scheduleReconnect()
    }
  }

  function disconnect() {
    manuallyClosed = true
    clearReconnectTimer()
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.close()
    } else {
      cleanupSocket()
    }
  }

  return {
    connect,
    disconnect,
    get readyState() {
      return ws?.readyState ?? WebSocket.CLOSED
    }
  }
}
