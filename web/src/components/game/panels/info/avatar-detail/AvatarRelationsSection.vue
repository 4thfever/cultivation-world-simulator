<script setup lang="ts">
import type { RelationInfo } from '@/types/core'
import RelationRow from '../components/RelationRow.vue'

type GroupedRelations = {
  parents: RelationInfo[]
  children: RelationInfo[]
  bloodOthers: RelationInfo[]
  others: RelationInfo[]
}

defineProps<{
  groupedRelations: GroupedRelations
  title: string
  mortalRealmText: string
  labelFor: (key: string) => string
  buildRelationMetaLines: (rel: RelationInfo) => string[]
  formatRelationSub: (rel: RelationInfo) => string
}>()

const emit = defineEmits<{
  (e: 'jump-avatar', id: string): void
}>()
</script>

<template>
  <div class="section" v-if="groupedRelations.parents.length || groupedRelations.children.length || groupedRelations.bloodOthers.length || groupedRelations.others.length">
    <div class="section-title">
      <slot name="icon" />
      {{ title }}
    </div>

    <div class="list-container">
      <template v-if="groupedRelations.parents.length">
        <template v-for="rel in groupedRelations.parents" :key="rel.target_id">
          <div v-if="rel.is_mortal" class="mortal-row">
            <span class="label">{{ labelFor(rel.label_key || '') }}</span>
            <span class="value">{{ mortalRealmText }}</span>
          </div>
          <RelationRow
            v-else
            :name="rel.name"
            :meta-lines="buildRelationMetaLines(rel)"
            :sub="formatRelationSub(rel)"
            :type="rel.relation_type"
            @click="emit('jump-avatar', rel.target_id)"
          />
        </template>
      </template>

      <template v-if="groupedRelations.children.length">
        <template v-for="rel in groupedRelations.children" :key="rel.target_id">
          <div v-if="rel.is_mortal" class="mortal-row">
            <span class="label">{{ rel.name }} ({{ rel.relation }})</span>
            <span class="value">{{ mortalRealmText }}</span>
          </div>
          <RelationRow
            v-else
            :name="rel.name"
            :meta-lines="buildRelationMetaLines(rel)"
            :sub="formatRelationSub(rel)"
            :type="rel.relation_type"
            @click="emit('jump-avatar', rel.target_id)"
          />
        </template>
      </template>

      <RelationRow
        v-for="rel in groupedRelations.bloodOthers"
        :key="rel.target_id"
        :name="rel.name"
        :meta-lines="buildRelationMetaLines(rel)"
        :sub="formatRelationSub(rel)"
        :type="rel.relation_type"
        @click="emit('jump-avatar', rel.target_id)"
      />

      <RelationRow
        v-for="rel in groupedRelations.others"
        :key="rel.target_id"
        :name="rel.name"
        :meta-lines="buildRelationMetaLines(rel)"
        :sub="formatRelationSub(rel)"
        :type="rel.relation_type"
        @click="emit('jump-avatar', rel.target_id)"
      />
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

.list-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mortal-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.mortal-row .label {
  color: #aaa;
}

.mortal-row .value {
  color: #666;
  font-size: 11px;
}
</style>
