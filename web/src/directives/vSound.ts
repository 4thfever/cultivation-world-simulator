import type { Directive } from 'vue';
import { useAudio } from '../composables/useAudio';
import type { SoundType } from '../composables/useAudio';

export const vSound: Directive = {
  mounted(el: HTMLElement, binding) {
    const { play } = useAudio();
    const type = (binding.arg || binding.value || 'click') as SoundType;
    
    // 标记该元素已有专用音效，全局监听器应跳过
    el.setAttribute('data-has-sound', type);

    el.addEventListener('click', () => {
      // 阻止事件冒泡可能会影响业务逻辑，所以这里不阻止
      play(type);
    });
  },
  // 动态更新
  updated(el: HTMLElement, binding) {
     const type = (binding.arg || binding.value || 'click') as SoundType;
     el.setAttribute('data-has-sound', type);
  }
};
