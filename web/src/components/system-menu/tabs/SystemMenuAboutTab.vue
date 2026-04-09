<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import folderGitIcon from '@/assets/icons/ui/lucide/folder-git-2.svg'
import usersIcon from '@/assets/icons/ui/lucide/users.svg'
import chevronRightIcon from '@/assets/icons/ui/lucide/chevron-right.svg'

const { t } = useI18n()

function openLink(url: string) {
  window.open(url, '_blank')
}
</script>

<template>
  <div class="other-panel-container">
    <div class="panel-header">
      <h3>{{ t('ui.about') }}</h3>
    </div>

    <div class="other-actions">
      <button
        class="custom-action-btn"
        @click="openLink('https://github.com/4thfever/cultivation-world-simulator')"
        v-sound
      >
        <div class="btn-content">
          <div class="btn-icon" :style="{ '--icon-url': `url(${folderGitIcon})` }" aria-hidden="true"></div>
          <div class="btn-text-group">
            <span class="btn-title">{{ t('ui.about_github') }}</span>
            <span class="btn-desc">{{ t('ui.about_github_desc') }}</span>
          </div>
        </div>
        <div class="btn-arrow" :style="{ '--icon-url': `url(${chevronRightIcon})` }" aria-hidden="true"></div>
      </button>

      <button
        class="custom-action-btn"
        @click="openLink('https://github.com/4thfever/cultivation-world-simulator/blob/main/CONTRIBUTORS.md')"
        v-sound
      >
        <div class="btn-content">
          <div class="btn-icon" :style="{ '--icon-url': `url(${usersIcon})` }" aria-hidden="true"></div>
          <div class="btn-text-group">
            <span class="btn-title">{{ t('ui.about_contributors') }}</span>
            <span class="btn-desc">{{ t('ui.about_contributors_desc') }}</span>
          </div>
        </div>
        <div class="btn-arrow" :style="{ '--icon-url': `url(${chevronRightIcon})` }" aria-hidden="true"></div>
      </button>
    </div>
  </div>
</template>

<style scoped>
.other-panel-container {
  max-width: 600px;
  margin: 0 auto;
  padding-top: 2em;
}

.panel-header {
  margin-bottom: 3em;
  text-align: center;
}

.panel-header h3 {
  margin: 0 0 0.5em 0;
  font-size: 1.5em;
  color: #eee;
}

.other-actions {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  padding: 0 40px;
}

.custom-action-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px 24px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  color: #eee;
  text-align: left;
}

.custom-action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.btn-icon {
  width: 24px;
  height: 24px;
  opacity: 0.8;
  flex-shrink: 0;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}

.btn-text-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.btn-title {
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 1px;
}

.btn-desc {
  font-size: 12px;
  color: #888;
}

.btn-arrow {
  width: 18px;
  height: 18px;
  opacity: 0.3;
  flex-shrink: 0;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}
</style>
