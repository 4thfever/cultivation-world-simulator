<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { RelationType } from '@/constants/relations'
import { avatarApi, type GameDataDTO, type CreateAvatarParams, type SimpleAvatarDTO } from '../../../../api'
import { useWorldStore } from '../../../../stores/world'
import { useMessage, NInput, NSelect, NSlider, NRadioGroup, NRadioButton, NForm, NFormItem, NButton } from 'naive-ui'
import { getAvatarPortraitUrl } from '@/utils/assetUrls'

const emit = defineEmits<{
  (e: 'created'): void
}>()

const { t, locale } = useI18n()
const worldStore = useWorldStore()
const message = useMessage()
const loading = ref(false)

const GENDER_MALE = '男'
const GENDER_FEMALE = '女'

const panelCopy = computed(() => {
  switch (locale.value) {
    case 'vi-VN':
      return {
        relationLabels: {
          [RelationType.TO_ME_IS_PARENT]: 'Cha mẹ',
          [RelationType.TO_ME_IS_CHILD]: 'Con cái',
          [RelationType.TO_ME_IS_SIBLING]: 'Anh chị em',
          [RelationType.TO_ME_IS_MASTER]: 'Sư phụ',
          [RelationType.TO_ME_IS_DISCIPLE]: 'Đệ tử',
          [RelationType.TO_ME_IS_LOVER]: 'Đạo lữ',
          [RelationType.TO_ME_IS_FRIEND]: 'Thân Thiện',
          [RelationType.TO_ME_IS_ENEMY]: 'Căm Ghét',
        },
        fetchFailed: 'Lấy dữ liệu trò chơi thất bại',
        createSuccess: 'Tạo nhân vật thành công',
        createFailed: 'Tạo nhân vật thất bại: ',
        loading: 'Đang tải dữ liệu...',
        labels: {
          name: 'Tên',
          gender: 'Giới tính',
          age: 'Tuổi',
          initialRealm: 'Cảnh giới ban đầu',
          sect: 'Tông môn',
          persona: 'Tính cách ban đầu',
          alignment: 'Lập trường',
          appearance: 'Ngoại hình',
          technique: 'Công pháp',
          weapon: 'Vũ khí',
          auxiliary: 'Trang bị phụ trợ',
          relations: 'Quan hệ',
        },
        placeholders: {
          surname: 'Họ',
          givenName: 'Tên',
          initialRealm: 'Chọn cảnh giới ban đầu',
          sect: 'Chọn tông môn (để trống nếu là tán tu)',
          persona: 'Chọn tính cách',
          technique: 'Chọn công pháp (có thể để trống)',
          weapon: 'Chọn vũ khí (có thể để trống)',
          auxiliary: 'Chọn trang bị phụ trợ (có thể để trống)',
          avatar: 'Chọn nhân vật',
          relation: 'Quan hệ',
        },
        buttons: {
          addRelation: '+ Thêm quan hệ',
          create: 'Tạo nhân vật',
        },
        avatarPlaceholder: 'Hãy chọn chân dung',
        noAvatars: 'Không có chân dung khả dụng',
        ageUnit: 'tuổi',
        genderLabels: {
          [GENDER_MALE]: 'Nam',
          [GENDER_FEMALE]: 'Nữ',
        },
      }
    case 'zh-TW':
      return {
        relationLabels: {
          [RelationType.TO_ME_IS_PARENT]: '父母',
          [RelationType.TO_ME_IS_CHILD]: '子女',
          [RelationType.TO_ME_IS_SIBLING]: '兄弟姐妹',
          [RelationType.TO_ME_IS_MASTER]: '師父',
          [RelationType.TO_ME_IS_DISCIPLE]: '徒弟',
          [RelationType.TO_ME_IS_LOVER]: '道侶',
          [RelationType.TO_ME_IS_FRIEND]: '友好',
          [RelationType.TO_ME_IS_ENEMY]: '憎惡',
        },
        fetchFailed: '取得遊戲資料失敗',
        createSuccess: '角色建立成功',
        createFailed: '建立失敗: ',
        loading: '載入資料中...',
        labels: {
          name: '姓名',
          gender: '性別',
          age: '年齡',
          initialRealm: '初始境界',
          sect: '所屬宗門',
          persona: '初始個性',
          alignment: '陣營',
          appearance: '顏值',
          technique: '功法',
          weapon: '兵器',
          auxiliary: '輔助裝備',
          relations: '人際關係',
        },
        placeholders: {
          surname: '姓',
          givenName: '名',
          initialRealm: '選擇初始境界',
          sect: '選擇宗門 (留空為散修)',
          persona: '選擇個性',
          technique: '選擇功法 (可留空)',
          weapon: '選擇兵器 (可留空)',
          auxiliary: '選擇輔助裝備 (可留空)',
          avatar: '選擇角色',
          relation: '關係',
        },
        buttons: {
          addRelation: '+ 添加關係',
          create: '建立角色',
        },
        avatarPlaceholder: '請選擇頭像',
        noAvatars: '暫無可用頭像',
        ageUnit: '歲',
        genderLabels: {
          [GENDER_MALE]: '男',
          [GENDER_FEMALE]: '女',
        },
      }
    case 'zh-CN':
      return {
        relationLabels: {
          [RelationType.TO_ME_IS_PARENT]: '父母',
          [RelationType.TO_ME_IS_CHILD]: '子女',
          [RelationType.TO_ME_IS_SIBLING]: '兄弟姐妹',
          [RelationType.TO_ME_IS_MASTER]: '师傅',
          [RelationType.TO_ME_IS_DISCIPLE]: '徒弟',
          [RelationType.TO_ME_IS_LOVER]: '道侣',
          [RelationType.TO_ME_IS_FRIEND]: '友好',
          [RelationType.TO_ME_IS_ENEMY]: '憎恶',
        },
        fetchFailed: '获取游戏数据失败',
        createSuccess: '角色创建成功',
        createFailed: '创建失败: ',
        loading: '加载数据中...',
        labels: {
          name: '姓名',
          gender: '性别',
          age: '年龄',
          initialRealm: '初始境界',
          sect: '所属宗门',
          persona: '初始个性',
          alignment: '阵营',
          appearance: '颜值',
          technique: '功法',
          weapon: '兵器',
          auxiliary: '辅助装备',
          relations: '人际关系',
        },
        placeholders: {
          surname: '姓',
          givenName: '名',
          initialRealm: '选择初始境界',
          sect: '选择宗门 (留空为散修)',
          persona: '选择个性',
          technique: '选择功法 (可留空)',
          weapon: '选择兵器 (可留空)',
          auxiliary: '选择辅助装备 (可留空)',
          avatar: '选择角色',
          relation: '关系',
        },
        buttons: {
          addRelation: '+ 添加关系',
          create: '创建角色',
        },
        avatarPlaceholder: '请选择头像',
        noAvatars: '暂无可用头像',
        ageUnit: '岁',
        genderLabels: {
          [GENDER_MALE]: '男',
          [GENDER_FEMALE]: '女',
        },
      }
    default:
      return {
        relationLabels: {
          [RelationType.TO_ME_IS_PARENT]: 'Parents',
          [RelationType.TO_ME_IS_CHILD]: 'Children',
          [RelationType.TO_ME_IS_SIBLING]: 'Siblings',
          [RelationType.TO_ME_IS_MASTER]: 'Master',
          [RelationType.TO_ME_IS_DISCIPLE]: 'Disciple',
          [RelationType.TO_ME_IS_LOVER]: 'Partner',
          [RelationType.TO_ME_IS_FRIEND]: 'Friendly',
          [RelationType.TO_ME_IS_ENEMY]: 'Hostile',
        },
        fetchFailed: 'Failed to fetch game data',
        createSuccess: 'Character created successfully',
        createFailed: 'Failed to create character: ',
        loading: 'Loading data...',
        labels: {
          name: 'Name',
          gender: 'Gender',
          age: 'Age',
          initialRealm: 'Initial Realm',
          sect: 'Sect',
          persona: 'Initial Persona',
          alignment: 'Alignment',
          appearance: 'Appearance',
          technique: 'Technique',
          weapon: 'Weapon',
          auxiliary: 'Auxiliary Gear',
          relations: 'Relations',
        },
        placeholders: {
          surname: 'Surname',
          givenName: 'Given name',
          initialRealm: 'Select initial realm',
          sect: 'Select sect (leave empty for rogue cultivator)',
          persona: 'Select persona',
          technique: 'Select technique (optional)',
          weapon: 'Select weapon (optional)',
          auxiliary: 'Select auxiliary gear (optional)',
          avatar: 'Select character',
          relation: 'Relation',
        },
        buttons: {
          addRelation: '+ Add relation',
          create: 'Create Character',
        },
        avatarPlaceholder: 'Please select an avatar',
        noAvatars: 'No avatars available',
        ageUnit: 'years old',
        genderLabels: {
          [GENDER_MALE]: 'Male',
          [GENDER_FEMALE]: 'Female',
        },
      }
  }
})

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
  { label: panelCopy.value.relationLabels[RelationType.TO_ME_IS_PARENT], value: RelationType.TO_ME_IS_PARENT },
  { label: panelCopy.value.relationLabels[RelationType.TO_ME_IS_CHILD], value: RelationType.TO_ME_IS_CHILD },
  { label: panelCopy.value.relationLabels[RelationType.TO_ME_IS_SIBLING], value: RelationType.TO_ME_IS_SIBLING },
  { label: panelCopy.value.relationLabels[RelationType.TO_ME_IS_MASTER], value: RelationType.TO_ME_IS_MASTER },
  { label: panelCopy.value.relationLabels[RelationType.TO_ME_IS_DISCIPLE], value: RelationType.TO_ME_IS_DISCIPLE },
  { label: panelCopy.value.relationLabels[RelationType.TO_ME_IS_LOVER], value: RelationType.TO_ME_IS_LOVER },
  { label: panelCopy.value.relationLabels[RelationType.TO_ME_IS_FRIEND], value: RelationType.TO_ME_IS_FRIEND },
  { label: panelCopy.value.relationLabels[RelationType.TO_ME_IS_ENEMY], value: RelationType.TO_ME_IS_ENEMY },
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
    label: `${w.name}（${t('game.info_panel.popup.types.' + w.type)}·${t('realms.' + w.grade)}）`,
    value: w.id
  }))
})

const auxiliaryOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.auxiliaries.map(a => ({
    label: `${a.name}（${t('realms.' + a.grade)}）`,
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
    const res = await avatarApi.fetchAvatarList()
    avatarList.value = res.avatars
  } catch (e) {
    message.error(panelCopy.value.fetchFailed)
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
    message.success(panelCopy.value.createSuccess)
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
    message.error(panelCopy.value.createFailed + String(e))
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
    <div v-if="loading && !gameData" class="loading">{{ panelCopy.loading }}</div>
    <div v-else class="create-layout">
      <div class="form-column">
        <n-form label-placement="left" label-width="80">
          <n-form-item :label="panelCopy.labels.name">
            <div class="name-inputs">
              <n-input v-model:value="createForm.surname" :placeholder="panelCopy.placeholders.surname" style="width: 6em" />
              <n-input v-model:value="createForm.given_name" :placeholder="panelCopy.placeholders.givenName" style="flex: 1" />
            </div>
          </n-form-item>
          <n-form-item :label="panelCopy.labels.gender">
            <n-radio-group v-model:value="createForm.gender">
              <n-radio-button :value="GENDER_MALE" :label="panelCopy.genderLabels[GENDER_MALE]" />
              <n-radio-button :value="GENDER_FEMALE" :label="panelCopy.genderLabels[GENDER_FEMALE]" />
            </n-radio-group>
          </n-form-item>
          <n-form-item :label="panelCopy.labels.age">
            <n-slider v-model:value="createForm.age" :min="16" :max="100" :step="1" />
            <span style="margin-left: 0.8em; width: 4.8em">{{ createForm.age }} {{ panelCopy.ageUnit }}</span>
          </n-form-item>
          <n-form-item :label="panelCopy.labels.initialRealm">
              <n-select v-model:value="createForm.level" :options="realmOptions" :placeholder="panelCopy.placeholders.initialRealm" />
          </n-form-item>
          <n-form-item :label="panelCopy.labels.sect">
            <n-select v-model:value="createForm.sect_id" :options="sectOptions" :placeholder="panelCopy.placeholders.sect" clearable />
          </n-form-item>
          <n-form-item :label="panelCopy.labels.persona">
            <n-select v-model:value="createForm.persona_ids" multiple :options="personaOptions" :placeholder="panelCopy.placeholders.persona" clearable max-tag-count="responsive" />
          </n-form-item>
          <n-form-item :label="panelCopy.labels.alignment">
            <n-select v-model:value="createForm.alignment" :options="alignmentOptions" :placeholder="t('ui.create_alignment_placeholder')" clearable />
          </n-form-item>
          <n-form-item :label="panelCopy.labels.appearance">
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
          <n-form-item :label="panelCopy.labels.technique">
            <n-select v-model:value="createForm.technique_id" :options="techniqueOptions" :placeholder="panelCopy.placeholders.technique" clearable />
          </n-form-item>
          <n-form-item :label="panelCopy.labels.weapon">
            <n-select v-model:value="createForm.weapon_id" :options="weaponOptions" :placeholder="panelCopy.placeholders.weapon" clearable />
          </n-form-item>
          <n-form-item :label="panelCopy.labels.auxiliary">
            <n-select v-model:value="createForm.auxiliary_id" :options="auxiliaryOptions" :placeholder="panelCopy.placeholders.auxiliary" clearable />
          </n-form-item>
          <n-form-item :label="panelCopy.labels.relations">
            <div class="relations-container">
              <div v-for="(rel, index) in createForm.relations" :key="index" class="relation-row">
                <n-select 
                  v-model:value="rel.target_id" 
                  :options="avatarOptions" 
                  :placeholder="panelCopy.placeholders.avatar" 
                  filterable 
                  style="width: 12em"
                />
                <n-select 
                  v-model:value="rel.relation" 
                  :options="relationOptions" 
                  :placeholder="panelCopy.placeholders.relation" 
                  style="width: 8em"
                />
                <n-button @click="removeRelation(index)" circle size="small" type="error">-</n-button>
              </div>
              <n-button @click="addRelation" size="small" dashed style="width: 100%">{{ panelCopy.buttons.addRelation }}</n-button>
            </div>
          </n-form-item>
          <div class="actions">
            <n-button type="primary" @click="handleCreateAvatar" block :loading="loading">{{ panelCopy.buttons.create }}</n-button>
          </div>
        </n-form>
      </div>
      <div class="avatar-column">
        <div class="avatar-preview">
          <img v-if="currentAvatarUrl" :src="currentAvatarUrl" alt="Avatar Preview" />
          <div v-else class="no-avatar">{{ panelCopy.avatarPlaceholder }}</div>
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
          <div v-if="availableAvatars.length === 0" class="no-avatars">{{ panelCopy.noAvatars }}</div>
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
