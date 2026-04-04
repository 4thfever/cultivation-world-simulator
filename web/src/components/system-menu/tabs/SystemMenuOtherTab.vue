<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits<{
  (e: 'return-to-main'): void
  (e: 'exit-game'): void
}>()
</script>

<template>
  <div class="other-panel-container">
    <div class="panel-header">
      <h3>{{ t('ui.other_options') }}</h3>
      <p class="description">{{ t('ui.other_options_desc') }}</p>
    </div>

    <div class="other-actions">
      <button class="custom-action-btn" @click="emit('return-to-main')" v-sound>
        <div class="btn-content">
          <div class="btn-icon">🏠</div>
          <div class="btn-text-group">
            <span class="btn-title">{{ t('ui.return_to_main') }}</span>
            <span class="btn-desc">{{ t('ui.return_to_main_desc') }}</span>
          </div>
        </div>
        <div class="btn-arrow">❯</div>
      </button>

      <button class="custom-action-btn danger-hover" @click="emit('exit-game')" v-sound>
        <div class="btn-content">
          <div class="btn-icon">🚪</div>
          <div class="btn-text-group">
            <span class="btn-title">{{ t('ui.quit_game') }}</span>
            <span class="btn-desc">{{ t('ui.quit_game_desc') }}</span>
          </div>
        </div>
        <div class="btn-arrow">❯</div>
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

.description {
  color: #888;
  font-size: 0.9em;
  margin: 0;
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

.danger-hover:hover {
  border-color: rgba(255, 80, 80, 0.4);
  background: linear-gradient(90deg, rgba(255, 80, 80, 0.05), rgba(255, 255, 255, 0.05));
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.btn-icon {
  font-size: 24px;
  opacity: 0.8;
  width: 32px;
  text-align: center;
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
  font-size: 18px;
  opacity: 0.3;
}
</style>
