<script setup lang="ts">
const props = defineProps<{
  presetId: string
}>()

const previewModules = import.meta.glob('@/assets/map-previews/*.svg', {
  eager: true,
  query: '?url',
  import: 'default',
}) as Record<string, string>

const previewByPreset = Object.fromEntries(
  Object.entries(previewModules).map(([path, url]) => {
    const filename = path.split('/').pop() ?? ''
    return [filename.replace(/\.svg$/u, ''), url]
  }),
) as Record<string, string>
</script>

<template>
  <div class="map-preset-preview">
    <img
      v-if="previewByPreset[props.presetId]"
      :src="previewByPreset[props.presetId]"
      alt=""
      draggable="false"
    >
    <div v-else class="map-preset-preview-fallback" aria-hidden="true" />
  </div>
</template>

<style scoped>
.map-preset-preview {
  flex: 0 0 78px;
  display: block;
  width: 100%;
  height: 78px;
  min-height: 78px;
  max-height: 78px;
  overflow: hidden;
  border-radius: 5px;
  background: #1f2933;
}

.map-preset-preview img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: fill;
}

.map-preset-preview-fallback {
  width: 100%;
  height: 100%;
  background:
    linear-gradient(135deg, rgba(132, 183, 112, 0.85) 0 48%, transparent 48%),
    linear-gradient(45deg, rgba(64, 132, 188, 0.8) 0 52%, transparent 52%),
    #245492;
}
</style>
