<script setup lang="ts">
defineProps<{
  testing: boolean
  label: string
}>()

const emit = defineEmits<{
  (e: 'save'): void
}>()
</script>

<template>
  <div class="action-bar">
    <button
      class="save-btn"
      :disabled="testing"
      @click="emit('save')"
    >
      {{ label }}
    </button>
  </div>
</template>

<style scoped>
.action-bar {
  display: flex;
  justify-content: flex-end;
  padding-bottom: 1.5em;
}

.save-btn {
  background: #2a8a4a;
  color: #fff;
  border: none;
  padding: 0.7em 1.5em;
  border-radius: 0.3em;
  font-size: 0.95em;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:hover:not(:disabled) {
  background: #3aa85a;
}

.save-btn:disabled {
  background: #33443a;
  color: #888;
  cursor: not-allowed;
}
</style>
