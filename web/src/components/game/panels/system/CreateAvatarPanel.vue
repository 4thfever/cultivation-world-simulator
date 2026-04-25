<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { NInput, NSelect, NSlider, NRadioGroup, NRadioButton, NForm, NFormItem, NButton } from 'naive-ui'
import { useCreateAvatarPanel } from '@/composables/useCreateAvatarPanel'

const emit = defineEmits<{
  (e: 'created'): void
}>()

const { t } = useI18n()

const {
  GENDER_MALE,
  GENDER_FEMALE,
  loading,
  gameData,
  createForm,
  relationOptions,
  sectOptions,
  personaOptions,
  realmOptions,
  techniqueOptions,
  weaponOptions,
  auxiliaryOptions,
  alignmentOptions,
  availableAvatars,
  currentAvatarUrl,
  avatarOptions,
  uiKey,
  addRelation,
  removeRelation,
  handleCreateAvatar,
  getAvatarPortraitUrl,
} = useCreateAvatarPanel(() => emit('created'))
</script>

<template>
  <div class="create-panel">
    <div v-if="loading && !gameData" class="loading">{{ t(uiKey('loading')) }}</div>
    <div v-else class="create-layout">
      <div class="form-column">
        <n-form label-placement="left" label-width="80">
          <n-form-item :label="t(uiKey('labels.name'))">
            <div class="name-inputs">
              <n-input v-model:value="createForm.surname" :placeholder="t(uiKey('placeholders.surname'))" style="width: 6em" />
              <n-input v-model:value="createForm.given_name" :placeholder="t(uiKey('placeholders.given_name'))" style="flex: 1" />
            </div>
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.gender'))">
            <n-radio-group v-model:value="createForm.gender">
              <n-radio-button :value="GENDER_MALE" :label="t(uiKey('gender_labels.male'))" />
              <n-radio-button :value="GENDER_FEMALE" :label="t(uiKey('gender_labels.female'))" />
            </n-radio-group>
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.age'))">
            <n-slider v-model:value="createForm.age" :min="16" :max="100" :step="1" />
            <span style="margin-left: 0.8em; width: 4.8em">{{ createForm.age }} {{ t(uiKey('age_unit')) }}</span>
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.initial_realm'))">
              <n-select v-model:value="createForm.level" :options="realmOptions" :placeholder="t(uiKey('placeholders.initial_realm'))" />
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.sect'))">
            <n-select v-model:value="createForm.sect_id" :options="sectOptions" :placeholder="t(uiKey('placeholders.sect'))" clearable />
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.persona'))">
            <n-select v-model:value="createForm.persona_ids" multiple :options="personaOptions" :placeholder="t(uiKey('placeholders.persona'))" clearable max-tag-count="responsive" />
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.alignment'))">
            <n-select v-model:value="createForm.alignment" :options="alignmentOptions" :placeholder="t('ui.create_alignment_placeholder')" clearable />
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.appearance'))">
            <div class="appearance-slider">
              <n-slider 
                v-model:value="createForm.appearance" 
                :min="1" 
                :max="10" 
                :step="1"
                style="flex: 1; min-width: 0;"
              />
              <span>{{ createForm.appearance || 1 }}</span>
            </div>
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.technique'))">
            <n-select v-model:value="createForm.technique_id" :options="techniqueOptions" :placeholder="t(uiKey('placeholders.technique'))" clearable />
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.weapon'))">
            <n-select v-model:value="createForm.weapon_id" :options="weaponOptions" :placeholder="t(uiKey('placeholders.weapon'))" clearable />
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.auxiliary'))">
            <n-select v-model:value="createForm.auxiliary_id" :options="auxiliaryOptions" :placeholder="t(uiKey('placeholders.auxiliary'))" clearable />
          </n-form-item>
          <n-form-item :label="t(uiKey('labels.relations'))">
            <div class="relations-container">
              <div v-for="(rel, index) in createForm.relations" :key="index" class="relation-row">
                <n-select 
                  v-model:value="rel.target_id" 
                  :options="avatarOptions" 
                  :placeholder="t(uiKey('placeholders.avatar'))" 
                  filterable 
                  style="width: 12em"
                />
                <n-select 
                  v-model:value="rel.relation" 
                  :options="relationOptions" 
                  :placeholder="t(uiKey('placeholders.relation'))" 
                  style="width: 8em"
                />
                <n-button @click="removeRelation(index)" circle size="small" type="error">-</n-button>
              </div>
              <n-button @click="addRelation" size="small" dashed style="width: 100%">{{ t(uiKey('buttons.add_relation')) }}</n-button>
            </div>
          </n-form-item>
          <div class="actions">
            <n-button type="primary" @click="handleCreateAvatar" block :loading="loading">{{ t(uiKey('buttons.create')) }}</n-button>
          </div>
        </n-form>
      </div>
      <div class="avatar-column">
        <div class="avatar-preview">
          <img v-if="currentAvatarUrl" :src="currentAvatarUrl" alt="Avatar Preview" />
          <div v-else class="no-avatar">{{ t(uiKey('avatar_placeholder')) }}</div>
        </div>
        <div class="avatar-grid">
          <div 
            v-for="id in availableAvatars" 
            :key="id"
            class="avatar-option"
            :class="{ selected: createForm.pic_id === id }"
            @click="createForm.pic_id = id"
          >
            <img :src="getAvatarPortraitUrl(createForm.gender, id)" loading="lazy" />
          </div>
          <div v-if="availableAvatars.length === 0" class="no-avatars">{{ t(uiKey('no_avatars')) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.create-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.loading {
  text-align: center;
  color: #888;
  padding: 3em;
}

.create-layout {
  display: flex;
  gap: 1.5em;
  height: 100%;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

.form-column {
  flex: 1;
  min-width: 20em;
}

.avatar-column {
  width: 20em;
  display: flex;
  flex-direction: column;
  gap: 0.8em;
}

.name-inputs {
  display: flex;
  gap: 0.8em;
}

.avatar-preview {
  width: 100%;
  height: 15em;
  border: 1px solid #444;
  border-radius: 0.3em;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #222;
  overflow: hidden;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.no-avatar {
  color: #666;
  font-size: 0.85em;
}

.avatar-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(4em, 1fr));
  grid-auto-rows: 5em;
  gap: 0.5em;
  padding: 0.4em;
  border: 1px solid #333;
  border-radius: 0.3em;
  min-height: 15em;
}

.avatar-option {
  width: 100%;
  height: 100%;
  border: 2px solid transparent;
  border-radius: 0.4em;
  overflow: hidden;
  cursor: pointer;
  background: #111;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s, transform 0.2s;
}

.avatar-option:hover {
  border-color: #666;
  transform: translateY(-2px);
}

.avatar-option.selected {
  border-color: #4a9eff;
}

.avatar-option img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 0.15em;
}

.no-avatars {
  grid-column: span 4;
  text-align: center;
  color: #666;
  font-size: 0.85em;
}

.appearance-slider {
  display: flex;
  align-items: center;
  gap: 0.8em;
  flex: 1;
  min-width: 0;
}

.appearance-slider :deep(.n-slider) {
  flex: 1;
  min-width: 0;
}

.appearance-slider span {
  width: 2.5em;
  text-align: right;
  color: #ddd;
}

.relations-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.6em;
}

.relation-row {
  display: flex;
  gap: 0.6em;
  align-items: center;
}

.actions {
  margin-top: 1.5em;
}
</style>
