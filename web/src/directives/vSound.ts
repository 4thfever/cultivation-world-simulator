import type { Directive } from 'vue';
import { useAudio } from '../composables/useAudio';
import type { SoundType } from '../composables/useAudio';

type SoundElement = HTMLElement & {
  __cwsSoundHandler?: () => void;
};

function resolveSoundType(el: HTMLElement, fallback: unknown): SoundType {
  return (el.getAttribute('data-has-sound') || fallback || 'click') as SoundType;
}

export const vSound: Directive = {
  mounted(el: SoundElement, binding) {
    const { play } = useAudio();
    const type = (binding.arg || binding.value || 'click') as SoundType;
    
    // 标记该元素已有专用音效，全局监听器应跳过
    el.setAttribute('data-has-sound', type);

    const handler = () => {
      // 阻止事件冒泡可能会影响业务逻辑，所以这里不阻止
      play(resolveSoundType(el, type));
    };
    el.__cwsSoundHandler = handler;
    el.addEventListener('click', handler);
  },
  // 动态更新
  updated(el: HTMLElement, binding) {
     const type = (binding.arg || binding.value || 'click') as SoundType;
     el.setAttribute('data-has-sound', type);
  },
  unmounted(el: SoundElement) {
    if (el.__cwsSoundHandler) {
      el.removeEventListener('click', el.__cwsSoundHandler);
      delete el.__cwsSoundHandler;
    }
    el.removeAttribute('data-has-sound');
  }
};
