<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { RelationType } from '@/constants/relations'
import { avatarApi, type GameDataDTO, type CreateAvatarParams, type SimpleAvatarDTO } from '../../../../api'
import { useWorldStore } from '../../../../stores/world'
import { useMessage, NInput, NSelect, NSlider, NRadioGroup, NRadioButton, NForm, NFormItem, NButton } from 'naive-ui'
import { getAvatarPortraitUrl } from '@/utils/assetUrls'
import { formatEntityGrade } from '@/utils/cultivationText'

const emit = defineEmits<{
  (e: 'created'): void
}>()

const { t } = useI18n()
const worldStore = useWorldStore()
const message = useMessage()
const loading = ref(false)

const GENDER_MALE = '男'
const GENDER_FEMALE = '女'

function uiKey(path: string): string {
  return `ui.create_avatar.${path}`
}

// --- State ---
const gameData = ref<GameDataDTO | null>(null)
const avatarMeta = ref<{ males: number[]; females: number[] } | null>(null)
const avatarList = ref<SimpleAvatarDTO[]>([]) // For relation selection

const createForm = ref<CreateAvatarParams>({
  surname: '',
  given_name: '',
  gender: GENDER_MALE,
  age: 16,
  level: undefined,
  sect_id: undefined,
  persona_ids: [],
  pic_id: undefined,
  technique_id: undefined,
  weapon_id: undefined,
  auxiliary_id: undefined,
  alignment: undefined,
  appearance: 7,
  relations: []
})

const relationOptions = computed(() => [
  { label: t(uiKey('relation_labels.parent')), value: RelationType.TO_ME_IS_PARENT },
  { label: t(uiKey('relation_labels.child')), value: RelationType.TO_ME_IS_CHILD },
  { label: t(uiKey('relation_labels.sibling')), value: RelationType.TO_ME_IS_SIBLING },
  { label: t(uiKey('relation_labels.master')), value: RelationType.TO_ME_IS_MASTER },
  { label: t(uiKey('relation_labels.disciple')), value: RelationType.TO_ME_IS_DISCIPLE },
  { label: t(uiKey('relation_labels.lover')), value: RelationType.TO_ME_IS_LOVER },
  { label: t(uiKey('relation_labels.friend')), value: RelationType.TO_ME_IS_FRIEND },
  { label: t(uiKey('relation_labels.enemy')), value: RelationType.TO_ME_IS_ENEMY },
])

// --- Computed Options ---
const sectOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.sects.map(s => ({ label: s.name, value: s.id }))
})

const personaOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.personas.map(p => ({ label: p.name + ` (${p.desc})`, value: p.id }))
})

const realmOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.realms.map((r, idx) => ({
    label: t(`realms.${r}`),
    value: idx * 30 + 1
  }))
})

const techniqueOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.techniques.map(item => ({
    label: `${item.name}（${t('attributes.' + item.attribute)}·${t('technique_grades.' + item.grade)}）`,
    value: item.id
  }))
})

const weaponOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.weapons.map(w => ({
    label: `${w.name}（${t('game.info_panel.popup.types.' + w.type)}·${formatEntityGrade(w.grade, t)}）`,
    value: w.id
  }))
})

const auxiliaryOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.auxiliaries.map(a => ({
    label: `${a.name}（${formatEntityGrade(a.grade, t)}）`,
    value: a.id
  }))
})

const alignmentOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.alignments.map(a => ({
    label: a.label,
    value: a.value
  }))
})

const availableAvatars = computed(() => {
  if (!avatarMeta.value) return []
  const key = createForm.value.gender === GENDER_FEMALE ? 'females' : 'males'
  return avatarMeta.value[key] || []
})

const currentAvatarUrl = computed(() => {
  return getAvatarPortraitUrl(createForm.value.gender, createForm.value.pic_id)
})

const avatarOptions = computed(() => {
  return avatarList.value.map(a => ({
    label: `[${a.sect_name}] ${a.name}`,
    value: a.id
  }))
})

// --- Methods ---
async function fetchData() {
  loading.value = true
  try {
    if (!gameData.value) {
      gameData.value = await avatarApi.fetchGameData()
    }
    if (!avatarMeta.value) {
      avatarMeta.value = await avatarApi.fetchAvatarMeta()
    }
    // 获取角色列表用于关系选择
    avatarList.value = await avatarApi.fetchAvatarList()
  } catch (e) {
    message.error(t(uiKey('fetch_failed')))
  } finally {
    loading.value = false
  }
}

function addRelation() {
  if (!createForm.value.relations) {
    createForm.value.relations = []
  }
  createForm.value.relations.push({ target_id: '', relation: RelationType.TO_ME_IS_FRIEND })
}

function removeRelation(index: number) {
  createForm.value.relations?.splice(index, 1)
}

async function handleCreateAvatar() {
  if (!createForm.value.level && realmOptions.value.length > 0) {
    createForm.value.level = realmOptions.value[0].value as number
  }

  loading.value = true
  try {
    const payload = { ...createForm.value }
    if (!payload.alignment) {
      payload.alignment = 'NEUTRAL'
    }
    
    await avatarApi.createAvatar(payload)
    message.success(t(uiKey('create_success')))
    await worldStore.fetchState?.()
    
    // Reset form
    createForm.value = {
      surname: '',
      given_name: '',
      gender: GENDER_MALE,
      age: 16,
      level: realmOptions.value[0]?.value,
      sect_id: undefined,
      persona_ids: [],
      pic_id: undefined,
      technique_id: undefined,
      weapon_id: undefined,
      auxiliary_id: undefined,
      alignment: undefined,
      appearance: 7,
      relations: []
    }
    
    emit('created')
  } catch (e) {
    message.error(t(uiKey('create_failed'), { error: String(e) }))
  } finally {
    loading.value = false
  }
}

watch(() => createForm.value.gender, () => {
  createForm.value.pic_id = undefined
})

watch(() => realmOptions.value, (options) => {
  if (!createForm.value.level && options.length > 0) {
    createForm.value.level = options[0].value as number
  }
}, { immediate: true })

onMounted(() => {
  fetchData()
})
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
