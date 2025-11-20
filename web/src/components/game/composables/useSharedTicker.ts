import { Ticker } from 'pixi.js'
import { onMounted, onUnmounted } from 'vue'

const sharedTicker = new Ticker()
let consumerCount = 0

export function useSharedTicker(callback: (delta: number) => void) {
  const runner = (ticker: Ticker) => {
    callback(ticker.deltaTime)
  }

  onMounted(() => {
    consumerCount += 1
    sharedTicker.add(runner)
    if (!sharedTicker.started) {
      sharedTicker.start()
    }
  })

  onUnmounted(() => {
    sharedTicker.remove(runner)
    consumerCount = Math.max(consumerCount - 1, 0)
    if (consumerCount === 0) {
      sharedTicker.stop()
    }
  })
}

