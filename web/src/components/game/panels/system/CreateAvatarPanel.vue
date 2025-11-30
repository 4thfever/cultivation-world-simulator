<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { gameApi, type GameDataDTO, type CreateAvatarParams, type SimpleAvatarDTO } from '../../../../api/game'
import { useWorldStore } from '../../../../stores/world'
import { useMessage, NInput, NSelect, NSlider, NRadioGroup, NRadioButton, NForm, NFormItem, NButton } from 'naive-ui'

const emit = defineEmits<{
  (e: 'created'): void
}>()

const worldStore = useWorldStore()
const message = useMessage()
const loading = ref(false)

// --- State ---
const gameData = ref<GameDataDTO | null>(null)
const avatarMeta = ref<{ males: number[]; females: number[] } | null>(null)
const avatarList = ref<SimpleAvatarDTO[]>([]) // For relation selection

const createForm = ref<CreateAvatarParams>({
  surname: '',
  given_name: '',
  gender: '男',
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

const relationOptions = [
  { label: '父母', value: 'parent' },
  { label: '子女', value: 'child' },
  { label: '兄弟姐妹', value: 'sibling' },
  { label: '师傅', value: 'master' },
  { label: '徒弟', value: 'apprentice' },
  { label: '道侣', value: 'lovers' },
  { label: '朋友', value: 'friend' },
  { label: '仇人', value: 'enemy' }
]

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
    label: r,
    value: idx * 30 + 1
  }))
})

const techniqueOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.techniques.map(t => ({
    label: `${t.name}（${t.attribute}·${t.grade}）`,
    value: t.id
  }))
})

const weaponOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.weapons.map(w => ({
    label: `${w.name}（${w.type}·${w.grade}）`,
    value: w.id
  }))
})

const auxiliaryOptions = computed(() => {
  if (!gameData.value) return []
  return gameData.value.auxiliaries.map(a => ({
    label: `${a.name}（${a.grade}）`,
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
  const key = createForm.value.gender === '女' ? 'females' : 'males'
  return avatarMeta.value[key] || []
})

const currentAvatarUrl = computed(() => {
  if (!createForm.value.pic_id) return ''
  const dir = createForm.value.gender === '女' ? 'females' : 'males'
  return `/assets/${dir}/${createForm.value.pic_id}.png`
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
      gameData.value = await gameApi.fetchGameData()
    }
    if (!avatarMeta.value) {
      avatarMeta.value = await gameApi.fetchAvatarMeta()
    }
    // 获取角色列表用于关系选择
    const res = await gameApi.fetchAvatarList()
    avatarList.value = res.avatars
  } catch (e) {
    message.error('获取游戏数据失败')
  } finally {
    loading.value = false
  }
}

function addRelation() {
  if (!createForm.value.relations) {
    createForm.value.relations = []
  }
  createForm.value.relations.push({ target_id: '', relation: 'friend' })
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
    await gameApi.createAvatar(createForm.value)
    message.success('角色创建成功')
    await worldStore.fetchState?.()
    
    // Reset form
    createForm.value = {
      surname: '',
      given_name: '',
      gender: '男',
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
    message.error('创建失败: ' + String(e))
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
    <div v-if="loading && !gameData" class="loading">加载数据中...</div>
    <div v-else class="create-layout">
      <div class="form-column">
        <n-form label-placement="left" label-width="80">
          <n-form-item label="姓名">
            <div class="name-inputs">
              <n-input v-model:value="createForm.surname" placeholder="姓" style="width: 80px" />
              <n-input v-model:value="createForm.given_name" placeholder="名" style="flex: 1" />
            </div>
          </n-form-item>
          <n-form-item label="性别">
            <n-radio-group v-model:value="createForm.gender">
              <n-radio-button value="男" label="男" />
              <n-radio-button value="女" label="女" />
            </n-radio-group>
          </n-form-item>
          <n-form-item label="年龄">
            <n-slider v-model:value="createForm.age" :min="16" :max="100" :step="1" />
            <span style="margin-left: 10px; width: 50px">{{ createForm.age }}岁</span>
          </n-form-item>
          <n-form-item label="初始境界">
              <n-select v-model:value="createForm.level" :options="realmOptions" placeholder="选择初始境界" />
          </n-form-item>
          <n-form-item label="所属宗门">
            <n-select v-model:value="createForm.sect_id" :options="sectOptions" placeholder="选择宗门 (留空为散修)" clearable />
          </n-form-item>
          <n-form-item label="初始个性">
            <n-select v-model:value="createForm.persona_ids" multiple :options="personaOptions" placeholder="选择个性" clearable max-tag-count="responsive" />
          </n-form-item>
          <n-form-item label="阵营">
            <n-select v-model:value="createForm.alignment" :options="alignmentOptions" placeholder="选择正/中/邪 (可留空)" clearable />
          </n-form-item>
          <n-form-item label="颜值">
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
          <n-form-item label="功法">
            <n-select v-model:value="createForm.technique_id" :options="techniqueOptions" placeholder="选择功法 (可留空)" clearable />
          </n-form-item>
          <n-form-item label="兵器">
            <n-select v-model:value="createForm.weapon_id" :options="weaponOptions" placeholder="选择兵器 (可留空)" clearable />
          </n-form-item>
          <n-form-item label="辅助装备">
            <n-select v-model:value="createForm.auxiliary_id" :options="auxiliaryOptions" placeholder="选择辅助装备 (可留空)" clearable />
          </n-form-item>
          <n-form-item label="人际关系">
            <div class="relations-container">
              <div v-for="(rel, index) in createForm.relations" :key="index" class="relation-row">
                <n-select 
                  v-model:value="rel.target_id" 
                  :options="avatarOptions" 
                  placeholder="选择角色" 
                  filterable 
                  style="width: 160px"
                />
                <n-select 
                  v-model:value="rel.relation" 
                  :options="relationOptions" 
                  placeholder="关系" 
                  style="width: 100px"
                />
                <n-button @click="removeRelation(index)" circle size="small" type="error">-</n-button>
              </div>
              <n-button @click="addRelation" size="small" dashed style="width: 100%">+ 添加关系</n-button>
            </div>
          </n-form-item>
          <div class="actions">
            <n-button type="primary" @click="handleCreateAvatar" block :loading="loading">创建角色</n-button>
          </div>
        </n-form>
      </div>
      <div class="avatar-column">
        <div class="avatar-preview">
          <img v-if="currentAvatarUrl" :src="currentAvatarUrl" alt="Avatar Preview" />
          <div v-else class="no-avatar">请选择头像</div>
        </div>
        <div class="avatar-grid">
          <div 
            v-for="id in availableAvatars" 
            :key="id"
            class="avatar-option"
            :class="{ selected: createForm.pic_id === id }"
            @click="createForm.pic_id = id"
          >
            <img :src="`/assets/${createForm.gender === '女' ? 'females' : 'males'}/${id}.png`" loading="lazy" />
          </div>
          <div v-if="availableAvatars.length === 0" class="no-avatars">暂无可用头像</div>
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
  padding: 40px;
}

.create-layout {
  display: flex;
  gap: 20px;
  height: 100%;
}

.form-column {
  flex: 1;
  min-width: 320px;
}

.avatar-column {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.name-inputs {
  display: flex;
  gap: 10px;
}

.avatar-preview {
  width: 100%;
  height: 220px;
  border: 1px solid #444;
  border-radius: 4px;
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
  font-size: 12px;
}

.avatar-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
  grid-auto-rows: 80px;
  gap: 8px;
  padding: 6px;
  border: 1px solid #333;
  border-radius: 4px;
  min-height: 220px;
}

.avatar-option {
  width: 100%;
  height: 100%;
  border: 2px solid transparent;
  border-radius: 6px;
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
  padding: 2px;
}

.no-avatars {
  grid-column: span 4;
  text-align: center;
  color: #666;
  font-size: 12px;
}

.appearance-slider {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.appearance-slider :deep(.n-slider) {
  flex: 1;
  min-width: 0;
}

.appearance-slider span {
  width: 32px;
  text-align: right;
  color: #ddd;
}

.relations-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.relation-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.actions {
  margin-top: 20px;
}
</style>
