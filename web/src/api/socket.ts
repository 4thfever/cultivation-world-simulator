/**
 * WebSocket Client
 * 纯粹的 Socket 封装，不依赖 Store
 */

export type MessageHandler = (data: any) => void;

export interface SocketOptions {
  url?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export class GameSocket {
  private ws: WebSocket | null = null;
  private handlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<(connected: boolean) => void> = new Set();
  
  private reconnectTimer: number | null = null;
  private attempts = 0;
  private isIntentionalClose = false;
  private options: SocketOptions;

  constructor(options: SocketOptions = {}) {
    this.options = options;
  }

  public connect() {
    this.isIntentionalClose = false;
    this.cleanup();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = this.options.url || `${protocol}//${host}/ws`;

    try {
      this.ws = new WebSocket(url);
      this.ws.onopen = this.onOpen.bind(this);
      this.ws.onmessage = this.onMessage.bind(this);
      this.ws.onclose = this.onClose.bind(this);
      this.ws.onerror = this.onError.bind(this);
    } catch (e) {
      console.error('WS Connection failed', e);
      this.scheduleReconnect();
    }
  }

  public disconnect() {
    this.isIntentionalClose = true;
    this.cleanup();
    this.notifyStatus(false);
  }

  public on(handler: MessageHandler) {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  public onStatusChange(handler: (connected: boolean) => void) {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  private onOpen() {
    this.attempts = 0;
    this.notifyStatus(true);
  }

  private onMessage(event: MessageEvent) {
    try {
      const data = JSON.parse(event.data);
      this.handlers.forEach(h => h(data));
    } catch (e) {
      console.warn('Failed to parse WS message', e);
    }
  }

  private onClose() {
    this.notifyStatus(false);
    if (!this.isIntentionalClose) {
      this.scheduleReconnect();
    }
  }

  private onError() {
    // Error usually precedes Close, so we handle logic in Close
  }

  private cleanup() {
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      this.ws.close();
      this.ws = null;
    }
  }

  private scheduleReconnect() {
    const max = this.options.maxReconnectAttempts ?? 10;
    if (this.attempts >= max) return;

    const base = this.options.reconnectInterval ?? 1000;
    const delay = Math.min(10000, base * (2 ** this.attempts));
    
    this.reconnectTimer = window.setTimeout(() => {
      this.attempts++;
      this.connect();
    }, delay);
  }

  private notifyStatus(connected: boolean) {
    this.statusHandlers.forEach(h => h(connected));
  }
}

// 单例实例
export const gameSocket = new GameSocket();

