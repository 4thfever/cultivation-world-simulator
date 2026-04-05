import { defineStore } from 'pinia';
import { computed, ref } from 'vue';

import i18n from '../locales';
import { defaultLocale, getHtmlLang, isEnabledLocale, type AppLocale } from '../locales/registry';
import { systemApi } from '../api/modules/system';
import type { AppSettingsDTO, RunConfigDTO } from '../types/api';
import { logWarn } from '../utils/appError';

function applyUiLocale(lang: string) {
  if (i18n.mode === 'legacy') {
    (i18n.global.locale as unknown as string) = lang;
  } else {
    (i18n.global.locale as unknown as { value: string }).value = lang;
  }

  document.documentElement.lang = getHtmlLang(lang);
}

function withContentLocale<T extends { content_locale: string }>(draft: T, locale: string): T {
  return {
    ...draft,
    content_locale: locale,
  };
}

export const useSettingStore = defineStore('setting', () => {
  const hydrated = ref(false);
  const loading = ref(false);

  const locale = ref<AppLocale>(defaultLocale);
  const sfxVolume = ref(0.5);
  const bgmVolume = ref(0.5);
  const isAutoSave = ref(false);
  const maxAutoSaves = ref(5);
  const newGameDraft = ref<RunConfigDTO>({
    content_locale: defaultLocale,
    init_npc_num: 9,
    sect_num: 3,
    npc_awakening_rate_per_month: 0.01,
    world_lore: '',
  });

  const isReady = computed(() => hydrated.value && !loading.value);

  function applySettings(settings: AppSettingsDTO) {
    locale.value = settings.ui.locale;
    bgmVolume.value = settings.ui.audio.bgm_volume;
    sfxVolume.value = settings.ui.audio.sfx_volume;
    isAutoSave.value = settings.simulation.auto_save_enabled;
    maxAutoSaves.value = settings.simulation.max_auto_saves;
    newGameDraft.value = withContentLocale({ ...settings.new_game_defaults }, settings.ui.locale);
    applyUiLocale(locale.value);
  }

  async function hydrate() {
    if (loading.value) return;

    loading.value = true;
    try {
      const settings = await systemApi.fetchSettings();
      applySettings(settings);
    } catch (e) {
      logWarn('SettingStore hydrate', e);
      applyUiLocale(locale.value);
    } finally {
      hydrated.value = true;
      loading.value = false;
    }
  }

  async function setLocale(lang: string) {
    const nextLocale = isEnabledLocale(lang) ? lang : defaultLocale
    const previous = locale.value;
    const previousDraft = { ...newGameDraft.value };
    locale.value = nextLocale;
    newGameDraft.value = withContentLocale({ ...newGameDraft.value }, nextLocale);
    applyUiLocale(nextLocale);

    try {
      const settings = await systemApi.patchSettings({
        ui: { locale: nextLocale },
        new_game_defaults: { content_locale: nextLocale },
      });
      applySettings(settings);
    } catch (e) {
      locale.value = previous;
      newGameDraft.value = previousDraft;
      applyUiLocale(previous);
      logWarn('SettingStore set locale', e);
    }
  }

  async function setSfxVolume(volume: number) {
    const previous = sfxVolume.value;
    sfxVolume.value = volume;

    try {
      const settings = await systemApi.patchSettings({ ui: { audio: { sfx_volume: volume } } });
      applySettings(settings);
    } catch (e) {
      sfxVolume.value = previous;
      logWarn('SettingStore set sfx volume', e);
    }
  }

  async function setBgmVolume(volume: number) {
    const previous = bgmVolume.value;
    bgmVolume.value = volume;

    try {
      const settings = await systemApi.patchSettings({ ui: { audio: { bgm_volume: volume } } });
      applySettings(settings);
    } catch (e) {
      bgmVolume.value = previous;
      logWarn('SettingStore set bgm volume', e);
    }
  }

  async function setAutoSave(enabled: boolean) {
    const previous = isAutoSave.value;
    isAutoSave.value = enabled;

    try {
      const settings = await systemApi.patchSettings({ simulation: { auto_save_enabled: enabled } });
      applySettings(settings);
    } catch (e) {
      isAutoSave.value = previous;
      logWarn('SettingStore set auto save', e);
    }
  }

  function updateNewGameDraft(patch: Partial<RunConfigDTO>) {
    newGameDraft.value = withContentLocale({
      ...newGameDraft.value,
      ...patch,
    }, locale.value);
  }

  async function saveNewGameDefaults() {
    const payload = withContentLocale({ ...newGameDraft.value }, locale.value);
    newGameDraft.value = payload;
    try {
      const settings = await systemApi.patchSettings({
        new_game_defaults: payload,
      });
      applySettings(settings);
      return true;
    } catch (e) {
      logWarn('SettingStore save new game defaults', e);
      return false;
    }
  }

  async function startGameWithDraft() {
    const saved = await saveNewGameDefaults();
    if (!saved) {
      throw new Error('Failed to save new game defaults');
    }
    return systemApi.startGame(withContentLocale({ ...newGameDraft.value }, locale.value));
  }

  return {
    hydrated,
    loading,
    isReady,
    locale,
    sfxVolume,
    bgmVolume,
    isAutoSave,
    maxAutoSaves,
    newGameDraft,
    hydrate,
    setLocale,
    setSfxVolume,
    setBgmVolume,
    setAutoSave,
    updateNewGameDraft,
    saveNewGameDefaults,
    startGameWithDraft,
  };
});
