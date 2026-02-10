import { useSettingStore } from '../stores/setting';

// 音频资源配置 - 使用 ogg 格式
const SOUND_URLS = {
  click: '/sfx/click.ogg',
  cancel: '/sfx/cancel.ogg',
  select: '/sfx/select.ogg',
  open: '/sfx/open.ogg',
} as const;

export type SoundType = keyof typeof SOUND_URLS;

// 单例模式维护 AudioContext 和 Buffers
let audioContext: AudioContext | null = null;
const buffers: Partial<Record<SoundType, AudioBuffer>> = {};

export function useAudio() {
  const settingStore = useSettingStore();

  // 1. 初始化并预加载 (建议在 main.ts 或 App.vue 挂载时调用)
  async function init() {
    if (typeof window === 'undefined') return;

    if (!audioContext) {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioContextClass) {
          audioContext = new AudioContextClass();
      } else {
          console.warn('Web Audio API is not supported in this browser.');
          return;
      }
    }
    
    // 预加载所有音效
    const loadPromises = Object.entries(SOUND_URLS).map(async ([key, url]) => {
      if (buffers[key as SoundType]) return; // 避免重复加载

      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const arrayBuffer = await response.arrayBuffer();
        if (audioContext) {
            const decodedBuffer = await audioContext.decodeAudioData(arrayBuffer);
            buffers[key as SoundType] = decodedBuffer;
        }
      } catch (e) {
        console.warn(`Failed to load sound: ${key} from ${url}`, e);
      }
    });

    await Promise.all(loadPromises);
  }

  // 2. 播放逻辑
  function play(type: SoundType = 'click') {
    if (settingStore.sfxVolume <= 0 || !audioContext || !buffers[type]) return;

    // 浏览器策略：如果 Context 被暂停（通常发生在无交互的页面加载时），需要恢复
    // 必须在用户交互事件中调用 resume
    if (audioContext.state === 'suspended') {
      audioContext.resume().catch(e => console.warn('Failed to resume audio context:', e));
    }

    const source = audioContext.createBufferSource();
    source.buffer = buffers[type]!;
    
    // 创建增益节点控制音量
    const gainNode = audioContext.createGain();
    gainNode.gain.value = settingStore.sfxVolume;
    
    source.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    source.start(0); // 立即播放，无延迟
  }

  return { init, play };
}
