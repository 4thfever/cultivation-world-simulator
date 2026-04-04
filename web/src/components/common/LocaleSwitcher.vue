<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { defaultLocale, localeRegistry, type AppLocale } from '@/locales/registry'
import { useSettingStore } from '@/stores/setting'

const props = withDefaults(defineProps<{
  variant?: 'splash' | 'settings'
}>(), {
  variant: 'settings',
})

const { t } = useI18n()
const settingStore = useSettingStore()

const isOpen = ref(false)
const shouldPulse = ref(false)
const rootRef = ref<HTMLElement | null>(null)
const hintTimer = ref<number | null>(null)

const locales = computed(() =>
  localeRegistry.filter((locale) => locale.enabled),
)

const currentLocaleLabel = computed(() => {
  return locales.value.find((locale) => locale.code === settingStore.locale)?.label ?? settingStore.locale
})

const currentLocaleShortLabel = computed(() => getLocaleShortLabel(settingStore.locale))

const splashAriaLabel = computed(() =>
  `${t('ui.language_switcher_button')} ${currentLocaleLabel.value}`,
)

function getLocaleShortLabel(locale: AppLocale | string) {
  switch (locale) {
    case 'zh-CN':
      return '简中'
    case 'zh-TW':
      return '繁中'
    case 'en-US':
      return 'EN'
    case 'vi-VN':
      return 'VI'
    case 'ja-JP':
      return '日本語'
    default:
      return String(locale).slice(0, 5).toUpperCase()
  }
}

function toggleOpen() {
  isOpen.value = !isOpen.value
}

async function handleSelect(localeCode: string) {
  await settingStore.setLocale(localeCode)
  isOpen.value = false
  shouldPulse.value = false
}

function handleDocumentPointerDown(event: MouseEvent) {
  const target = event.target
  if (!(target instanceof Node)) return
  if (rootRef.value?.contains(target)) return
  isOpen.value = false
}

function clearHintTimer() {
  if (hintTimer.value !== null) {
    window.clearTimeout(hintTimer.value)
    hintTimer.value = null
  }
}

function setupSplashHint() {
  clearHintTimer()

  if (
    props.variant !== 'splash'
    || settingStore.locale !== defaultLocale
    || typeof window === 'undefined'
  ) {
    shouldPulse.value = false
    return
  }

  const sessionKey = 'cws-language-hint-shown'
  if (window.sessionStorage.getItem(sessionKey) === '1') {
    shouldPulse.value = false
    return
  }

  shouldPulse.value = true
  hintTimer.value = window.setTimeout(() => {
    shouldPulse.value = false
    window.sessionStorage.setItem(sessionKey, '1')
  }, 2400)
}

watch(() => settingStore.locale, () => {
  setupSplashHint()
})

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  setupSplashHint()
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  clearHintTimer()
})
</script>

<template>
  <div
    ref="rootRef"
    class="locale-switcher"
    :class="[`locale-switcher--${props.variant}`, { 'is-open': isOpen, 'is-pulsing': shouldPulse }]"
  >
    <button
      v-if="props.variant === 'splash'"
      type="button"
      class="locale-trigger locale-trigger--splash"
      :aria-expanded="isOpen"
      :aria-label="splashAriaLabel"
      @click="toggleOpen"
    >
      <span class="locale-trigger__icon" aria-hidden="true">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
          <circle cx="32" cy="32" r="22" fill="none" stroke="currentColor" stroke-width="4"/>
          <path d="M10 32h44M32 10c6.5 6.2 10 13.5 10 22s-3.5 15.8-10 22c-6.5-6.2-10-13.5-10-22s3.5-15.8 10-22Z" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/>
          <path d="M17 19.5c4.6 2.6 9.7 4 15 4s10.4-1.4 15-4M17 44.5c4.6-2.6 9.7-4 15-4s10.4 1.4 15 4" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
        </svg>
      </span>
      <span class="locale-trigger__text">
        <span class="locale-trigger__title">{{ t('ui.language_switcher_button') }}</span>
        <span class="locale-trigger__value">{{ currentLocaleShortLabel }}</span>
      </span>
      <span class="locale-trigger__caret" aria-hidden="true">▾</span>
    </button>

    <div
      v-else
      class="locale-select-inline"
    >
      <button
        type="button"
        class="locale-trigger locale-trigger--settings"
        :aria-expanded="isOpen"
        :aria-label="splashAriaLabel"
        @click="toggleOpen"
      >
        <span class="locale-trigger__icon" aria-hidden="true">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
            <circle cx="32" cy="32" r="22" fill="none" stroke="currentColor" stroke-width="4"/>
            <path d="M10 32h44M32 10c6.5 6.2 10 13.5 10 22s-3.5 15.8-10 22c-6.5-6.2-10-13.5-10-22s3.5-15.8 10-22Z" fill="none" stroke="currentColor" stroke-width="4" stroke-linejoin="round"/>
            <path d="M17 19.5c4.6 2.6 9.7 4 15 4s10.4-1.4 15-4M17 44.5c4.6-2.6 9.7-4 15-4s10.4 1.4 15 4" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
          </svg>
        </span>
        <span class="locale-trigger__settings-label">{{ currentLocaleLabel }}</span>
        <span class="locale-trigger__caret" aria-hidden="true">▾</span>
      </button>
    </div>

    <transition name="locale-fade">
      <div v-if="isOpen" class="locale-panel" role="menu">
        <div class="locale-panel__header">
          <div class="locale-panel__title">{{ t('ui.language_switcher_button') }}</div>
          <div class="locale-panel__subtitle">{{ t('ui.language_switcher_hint') }}</div>
        </div>

        <button
          v-for="locale in locales"
          :key="locale.code"
          type="button"
          class="locale-option"
          :class="{ 'is-active': locale.code === settingStore.locale }"
          role="menuitemradio"
          :aria-checked="locale.code === settingStore.locale"
          @click="handleSelect(locale.code)"
        >
          <span class="locale-option__label">{{ locale.label }}</span>
          <span v-if="locale.code === settingStore.locale" class="locale-option__check" aria-hidden="true">✓</span>
        </button>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.locale-switcher {
  position: relative;
}

.locale-switcher--splash {
  position: absolute;
  top: 24px;
  right: 24px;
  z-index: 3;
}

.locale-trigger {
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(16, 20, 26, 0.58);
  color: #f3f0e8;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  transition: border-color 0.2s ease, background-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.locale-trigger:hover {
  background: rgba(24, 30, 38, 0.8);
  border-color: rgba(255, 255, 255, 0.34);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.3);
}

.locale-trigger--splash {
  padding: 10px 14px 10px 12px;
  border-radius: 999px;
  width: 196px;
  justify-content: space-between;
}

.locale-trigger--settings {
  min-width: 240px;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: 12px;
}

.locale-trigger__icon {
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0.95;
  flex-shrink: 0;
}

.locale-trigger__icon svg {
  width: 100%;
  height: 100%;
}

.locale-trigger__text {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.locale-trigger__title {
  font-size: 12px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  opacity: 0.82;
}

.locale-trigger__value,
.locale-trigger__settings-label {
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
}

.locale-trigger__value {
  min-width: 44px;
  text-align: right;
}

.locale-trigger__caret {
  font-size: 12px;
  opacity: 0.62;
}

.locale-panel {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  width: 280px;
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(12, 15, 21, 0.94);
  box-shadow: 0 20px 44px rgba(0, 0, 0, 0.34);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.locale-panel__header {
  padding: 6px 8px 10px;
}

.locale-panel__title {
  color: #f6f2ea;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.01em;
}

.locale-panel__subtitle {
  margin-top: 4px;
  color: rgba(243, 240, 232, 0.7);
  font-size: 12px;
}

.locale-option {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 0;
  background: transparent;
  color: #f3f0e8;
  text-align: left;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background-color 0.18s ease, transform 0.18s ease;
}

.locale-option:hover {
  background: rgba(255, 255, 255, 0.07);
  transform: translateX(1px);
}

.locale-option.is-active {
  background: rgba(84, 102, 141, 0.34);
}

.locale-option__label {
  font-size: 15px;
}

.locale-option__check {
  color: #9dc0ff;
  font-weight: 700;
}

.is-pulsing .locale-trigger--splash {
  animation: localePulse 0.85s ease-in-out 2 alternate;
}

.locale-fade-enter-active,
.locale-fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.locale-fade-enter-from,
.locale-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@keyframes localePulse {
  from {
    border-color: rgba(255, 255, 255, 0.18);
    box-shadow: 0 0 0 rgba(124, 173, 255, 0);
  }
  to {
    border-color: rgba(157, 192, 255, 0.48);
    box-shadow: 0 0 0 5px rgba(124, 173, 255, 0.08);
  }
}

@media (max-width: 768px) {
  .locale-switcher--splash {
    top: 16px;
    right: 16px;
  }

  .locale-trigger--splash {
    width: 188px;
    padding: 9px 12px;
  }

  .locale-panel {
    width: min(280px, calc(100vw - 32px));
  }
}
</style>
