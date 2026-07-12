<script setup lang="ts">
type ParsedEffect = {
  id: string
  source: string
  segments: string[]
}

defineProps<{
  effects: ParsedEffect[]
  title: string
}>()
</script>

<template>
  <div class="section" v-if="effects.length">
    <div class="section-title">
      <slot name="icon" />
      {{ title }}
    </div>
    <div class="effects-list">
      <div
        v-for="effect in effects"
        :key="effect.id"
        class="effect-row"
      >
        <div class="effect-source">{{ effect.source }}</div>
        <div class="effect-content">
          <div v-for="(segment, sIdx) in effect.segments" :key="`${effect.id}-${sIdx}`">
            {{ segment }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: bold;
  color: #9f9380;
  border-bottom: 1px solid rgba(175, 148, 105, 0.32);
  padding-bottom: 4px;
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}

.effects-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 12px;
}

.effect-row {
  display: grid;
  grid-template-columns: minmax(84px, 38%) minmax(0, 1fr);
  gap: 6px 12px;
  align-items: start;
}

.effect-source {
  color: #888;
  text-align: right;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  line-height: 1.35;
}

.effect-content {
  color: #aaddff;
  line-height: 1.4;
  min-width: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

@media (max-width: 420px) {
  .effect-row {
    grid-template-columns: minmax(0, 1fr);
    gap: 4px;
  }

  .effect-source {
    text-align: left;
  }
}
</style>
