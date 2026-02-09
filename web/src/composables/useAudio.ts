import { useSettingStore } from '../stores/setting';

const sounds = {
  click: new Audio('/sfx/click.ogg'),
  cancel: new Audio('/sfx/cancel.ogg'),
  select: new Audio('/sfx/select.ogg'),
  open: new Audio('/sfx/open.ogg'),
};

export type SoundType = keyof typeof sounds;

export function useAudio() {
  function play(type: SoundType = 'click') {
    const settingStore = useSettingStore();
    
    if (!settingStore.sfxEnabled) return;

    const audio = sounds[type];
    if (audio) {
      audio.currentTime = 0;
      audio.volume = settingStore.sfxVolume;
      audio.play().catch(() => {
        // Ignore auto-play policy errors
      });
    }
  }

  return {
    play
  };
}
