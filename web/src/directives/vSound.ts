import type { Directive } from 'vue';
import { useAudio } from '../composables/useAudio';
import type { SoundType } from '../composables/useAudio';

export const vSound: Directive = {
  mounted(el: HTMLElement, binding) {
    const { play } = useAudio();
    const type = (binding.arg || binding.value || 'click') as SoundType;
    
    el.addEventListener('click', (e) => {
      // 阻止事件冒泡可能会影响业务逻辑，所以这里不阻止
      play(type);
    });
    
    // 如果需要 hover 音效，可以在这里添加 mouseenter 监听
    // 但根据需求，不需要 hover 音效
  }
};
