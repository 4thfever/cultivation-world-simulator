<script setup lang="ts">
import { NPopover } from 'naive-ui'

interface Props {
  label: string
  icon?: string
  color?: string
  disablePopover?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  color: '#ccc',
  disablePopover: false,
})

const emit = defineEmits(['trigger-click'])
</script>

<template>
  <div class="status-widget">
    <span class="divider">|</span>

    <span
      v-if="disablePopover"
      class="widget-trigger"
      :style="{ color: props.color }"
      :title="props.label"
      @click="emit('trigger-click')"
      v-sound="'open'"
    >
      <span v-if="props.icon" class="widget-icon" :style="{ '--icon-url': `url(${props.icon})` }" aria-hidden="true"></span>
      <span class="widget-label">{{ props.label }}</span>
    </span>

    <n-popover v-else trigger="click" placement="bottom" style="max-width: 600px;">
      <template #trigger>
        <span
          class="widget-trigger"
          :style="{ color: props.color }"
          :title="props.label"
          @click="emit('trigger-click')"
          v-sound="'open'"
        >
          <span v-if="props.icon" class="widget-icon" :style="{ '--icon-url': `url(${props.icon})` }" aria-hidden="true"></span>
          <span class="widget-label">{{ props.label }}</span>
        </span>
      </template>

      <div class="widget-content">
        <slot name="single"></slot>
      </div>
    </n-popover>
  </div>
</template>

<style scoped>
.status-widget {
  min-width: 0;
  flex: 0 1 auto;
}

.widget-trigger {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: bold;
  transition: opacity 0.2s, color 0.2s;
  white-space: nowrap;
  min-width: 0;
  max-width: 100%;
  flex-shrink: 1;
}

.widget-trigger:hover {
  opacity: 0.92;
}

.divider {
  color: #4a443b;
  margin-right: 10px;
}

.widget-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.widget-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  display: inline-block;
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
