<script setup lang="ts">
import type { EffectEntity } from '@/types/core'
import type { AvatarAdjustCategory } from '@/composables/useAvatarDetailPanel'
import EntityRow from '../components/EntityRow.vue'
import pencilLineIcon from '@/assets/icons/ui/lucide/pencil-line.svg'

type EquipmentSlot = {
  category: Exclude<AvatarAdjustCategory, 'personas'>
  label: string
  icon: string
  item: EffectEntity | null
  meta?: string
}

defineProps<{
  slots: EquipmentSlot[]
  spiritAnimal?: EffectEntity
  emptyText: string
  adjustTitle: string
}>()

const emit = defineEmits<{
  (e: 'show-detail', item: EffectEntity | undefined): void
  (e: 'adjust', category: AvatarAdjustCategory): void
}>()
</script>

<template>
  <div class="section">
    <div class="equipment-slots plain">
      <div
        v-for="slot in slots"
        :key="slot.category"
        class="equipment-slot-block"
      >
        <div class="section-title subsection-title">
          <span class="section-title-icon" :style="{ '--icon-url': `url(${slot.icon})` }" aria-hidden="true"></span>
          {{ slot.label }}
        </div>
        <div class="adjustable-row">
          <EntityRow
            v-if="slot.item"
            :item="slot.item"
            :meta="slot.meta"
            details-below
            @click="emit('show-detail', slot.item)"
          />
          <div v-else class="empty-row slot-empty">{{ emptyText }}</div>
          <button
            class="adjust-btn inline"
            :title="adjustTitle"
            :aria-label="adjustTitle"
            @click="emit('adjust', slot.category)"
          >
            <span class="adjust-icon" :style="{ '--icon-url': `url(${pencilLineIcon})` }" aria-hidden="true"></span>
          </button>
        </div>
      </div>
    </div>
    <EntityRow
      v-if="spiritAnimal"
      :item="spiritAnimal"
      details-below
      @click="emit('show-detail', spiritAnimal)"
    />
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

.equipment-slots {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.equipment-slots.plain {
  gap: 8px;
}

.equipment-slot-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subsection-title {
  margin-bottom: 2px;
  color: #a99a84;
}

.adjustable-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: center;
}

.empty-row {
  padding: 6px 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.03);
  color: #777;
  font-size: 12px;
}

.adjust-btn {
  border: none;
  background: transparent;
  color: #8a8a8a;
  font-size: 11px;
  cursor: pointer;
  padding: 1px 0 1px 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 0;
  opacity: 0.62;
  transition: opacity 0.18s ease;
}

.adjust-btn:hover {
  opacity: 0.95;
}

.adjust-btn.inline {
  width: 22px;
  min-height: 22px;
  padding: 0;
}

.adjust-icon,
.section-title-icon {
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
  flex-shrink: 0;
}

.adjust-icon {
  width: 13px;
  height: 13px;
}

.section-title-icon {
  width: 1em;
  height: 1em;
}
</style>
