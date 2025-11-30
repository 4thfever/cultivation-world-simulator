<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { gameApi, type GameDataDTO, type SimpleAvatarDTO, type CreateAvatarParams } from '../api/game'
import { useWorldStore } from '../stores/world'
import { useUiStore } from '../stores/ui'
import { useMessage, NInput, NSelect, NSlider, NRadioGroup, NRadioButton, NForm, NFormItem, NButton } from 'naive-ui'
import type { SaveFileDTO } from '../types/api'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const worldStore = useWorldStore()
const uiStore = useUiStore()
const message = useMessage()

const activeTab = ref<'save' | 'load' | 'create' | 'delete'>('load')
const saves = ref<SaveFileDTO[]>([])
const loading = ref(false)

// --- Create Avatar State ---
const gameData = ref<GameDataDTO | null>(null)
const avatarMeta = ref<{ males: number[]; females: number[] } | null>(null)
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

// --- Delete Avatar State ---
const avatarList = ref<SimpleAvatarDTO[]>([])
const avatarSearch = ref('')

const filteredAvatars = computed(() => {
  if (!avatarSearch.value) return avatarList.value
  return avatarList.value.filter(a => a.name.includes(avatarSearch.value))
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

// --- Options ---

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

const avatarOptions = computed(() => {
  return avatarList.value.map(a => ({
    label: `[${a.sect_name}] ${a.name}`,
    value: a.id
  }))
})

function addRelation() {
  if (!createForm.value.relations) {
    createForm.value.relations = []
  }
  createForm.value.relations.push({ target_id: '', relation: 'friend' })
}

function removeRelation(index: number) {
  createForm.value.relations?.splice(index, 1)
}

// --- Actions ---

async function fetchSaves() {
  loading.value = true
  try {
    const res = await gameApi.fetchSaves()
    saves.value = res.saves
  } catch (e) {
    message.error('获取存档列表失败')
  } finally {
    loading.value = false
  }
}

async function fetchGameData() {
  loading.value = true
  try {
    if (!gameData.value) {
      gameData.value = await gameApi.fetchGameData()
    }
    if (!avatarMeta.value) {
      avatarMeta.value = await gameApi.fetchAvatarMeta()
    }
  } catch (e) {
    message.error('获取游戏数据失败')
  } finally {
    loading.value = false
  }
}

async function fetchAvatarList() {
  loading.value = true
  try {
    const res = await gameApi.fetchAvatarList()
    avatarList.value = res.avatars
  } catch (e) {
    message.error('获取角色列表失败')
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  loading.value = true
  try {
    const res = await gameApi.saveGame()
    message.success(`存档成功: ${res.filename}`)
    await fetchSaves()
  } catch (e) {
    message.error('存档失败')
  } finally {
    loading.value = false
  }
}

async function handleLoad(filename: string) {
  if (!confirm(`确定要加载存档 ${filename} 吗？当前未保存的进度将丢失。`)) return

  loading.value = true
  try {
    await gameApi.loadGame(filename)
    worldStore.reset()
    uiStore.clearSelection()
    uiStore.clearHoverCache()
    await worldStore.initialize()
    message.success('读档成功')
    emit('close')
  } catch (e) {
    message.error('读档失败')
  } finally {
    loading.value = false
  }
}

async function handleCreateAvatar() {
  if (!createForm.value.level && realmOptions.value.length > 0) {
    createForm.value.level = realmOptions.value[0].value as number
  }

  loading.value = true
  try {
    await gameApi.createAvatar(createForm.value)
    message.success('角色创建成功')
    await Promise.all([
      fetchAvatarList(),
      worldStore.fetchState ? worldStore.fetchState() : Promise.resolve()
    ])
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
  } catch (e) {
    message.error('创建失败: ' + String(e))
  } finally {
    loading.value = false
  }
}

async function handleDeleteAvatar(id: string, name: string) {
  if (!confirm(`确定要删除角色 ${name} 吗？此操作不可恢复。`)) return
  
  loading.value = true
  try {
    await gameApi.deleteAvatar(id)
    message.success('删除成功')
    await Promise.all([
      fetchAvatarList(),
      worldStore.fetchState ? worldStore.fetchState() : Promise.resolve()
    ])
  } catch (e) {
    message.error('删除失败')
  } finally {
    loading.value = false
  }
}

function switchTab(tab: typeof activeTab.value) {
  activeTab.value = tab
  if (tab === 'save' || tab === 'load') {
    fetchSaves()
  } else if (tab === 'create') {
    fetchGameData()
    fetchAvatarList()
  } else if (tab === 'delete') {
    fetchAvatarList()
  }
}

watch(() => createForm.value.gender, () => {
  createForm.value.pic_id = undefined
})

watch(() => props.visible, (val) => {
  if (val) {
    switchTab(activeTab.value)
  }
})

watch(() => realmOptions.value, (options) => {
  if (!createForm.value.level && options.length > 0) {
    createForm.value.level = options[0].value as number
  }
}, { immediate: true })

onMounted(() => {
  if (props.visible) {
    fetchSaves()
  }
})

</script>

<template>
  <div v-if="visible" class="system-menu-overlay" @click.self="emit('close')">
    <div class="system-menu">
      <div class="menu-header">
        <h2>系统菜单</h2>
        <button class="close-btn" @click="emit('close')">×</button>
      </div>
      
      <div class="menu-tabs">
        <button 
          :class="{ active: activeTab === 'load' }"
          @click="switchTab('load')"
        >
          加载游戏
        </button>
        <button 
          :class="{ active: activeTab === 'save' }"
          @click="switchTab('save')"
        >
          保存游戏
        </button>
        <button 
          :class="{ active: activeTab === 'create' }"
          @click="switchTab('create')"
        >
          新建角色
        </button>
        <button 
          :class="{ active: activeTab === 'delete' }"
          @click="switchTab('delete')"
        >
          删除角色
        </button>
      </div>

      <div class="menu-content">
        <div v-if="loading" class="loading">处理中...</div>
        
        <!-- Save Panel -->
        <div v-else-if="activeTab === 'save'" class="save-panel">
          <div class="new-save-card" @click="handleSave">
            <div class="icon">+</div>
            <div>新建存档</div>
            <div class="sub">点击创建一个新的存档文件</div>
          </div>
        </div>

        <!-- Load Panel -->
        <div v-else-if="activeTab === 'load'" class="load-panel">
          <div v-if="saves.length === 0" class="empty">暂无存档</div>
          <div 
            v-for="save in saves" 
            :key="save.filename"
            class="save-item"
            @click="handleLoad(save.filename)"
          >
            <div class="save-info">
              <div class="save-time">{{ save.save_time }}</div>
              <div class="game-time">游戏时间: {{ save.game_time }}</div>
              <div class="filename">{{ save.filename }}</div>
            </div>
            <div class="load-btn">加载</div>
          </div>
        </div>

        <!-- Create Avatar Panel -->
        <div v-else-if="activeTab === 'create'" class="create-panel">
          <div class="create-layout">
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
                  <n-button type="primary" @click="handleCreateAvatar" block>创建角色</n-button>
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

        <!-- Delete Avatar Panel -->
        <div v-else-if="activeTab === 'delete'" class="delete-panel">
          <div class="search-bar">
            <n-input v-model:value="avatarSearch" placeholder="搜索角色名..." />
          </div>
          <div class="avatar-list">
            <div v-if="filteredAvatars.length === 0" class="empty">未找到角色</div>
            <div 
              v-for="avatar in filteredAvatars" 
              :key="avatar.id"
              class="avatar-item"
            >
               <div class="avatar-info">
                 <div class="name">{{ avatar.name }}</div>
                 <div class="details">
                    {{ avatar.gender }} | {{ avatar.age }}岁 | {{ avatar.realm }} | {{ avatar.sect_name }}
                 </div>
               </div>
               <n-button type="error" size="small" @click="handleDeleteAvatar(avatar.id, avatar.name)">删除</n-button>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<style scoped>
.system-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.system-menu {
  background: #1a1a1a;
  width: 820px;
  height: 620px;
  border: 1px solid #333;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.menu-header {
  padding: 16px;
  border-bottom: 1px solid #333;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-header h2 {
  margin: 0;
  font-size: 18px;
  color: #ddd;
}

.close-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 24px;
  cursor: pointer;
}

.menu-tabs {
  display: flex;
  border-bottom: 1px solid #333;
}

.menu-tabs button {
  flex: 1;
  padding: 12px;
  background: #222;
  border: none;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
}

.menu-tabs button:hover {
  background: #2a2a2a;
}

.menu-tabs button.active {
  background: #1a1a1a;
  color: #fff;
  border-bottom: 2px solid #4a9eff;
}

.menu-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.save-panel, .load-panel, .create-panel, .delete-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.save-panel {
    align-items: center;
  padding-top: 40px;
}

.new-save-card {
  width: 200px;
  height: 150px;
  border: 2px dashed #444;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  color: #888;
}

.new-save-card:hover {
  border-color: #666;
  background: #222;
  color: #fff;
}

.new-save-card .icon {
  font-size: 40px;
  margin-bottom: 10px;
}

.new-save-card .sub {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.save-item, .avatar-item {
  background: #222;
  border: 1px solid #333;
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  transition: background 0.2s;
}

.save-item:hover, .avatar-item:hover {
  background: #2a2a2a;
  border-color: #444;
}

.save-info .save-time, .avatar-info .name {
  color: #fff;
  font-weight: bold;
  font-size: 14px;
}

.save-info .game-time {
  color: #4a9eff;
  font-size: 13px;
  margin: 4px 0;
}

.save-info .filename {
  color: #666;
  font-size: 12px;
  font-family: monospace;
}

.avatar-info .details {
    color: #888;
    font-size: 12px;
    margin-top: 4px;
}

.load-btn {
  background: #333;
  color: #ddd;
  border: 1px solid #444;
  padding: 6px 16px;
  border-radius: 4px;
}

.loading {
  text-align: center;
  color: #888;
  padding: 40px;
}

.empty {
  text-align: center;
  color: #666;
  padding: 40px;
}

.create-panel .actions {
    margin-top: 20px;
}

.search-bar {
    margin-bottom: 15px;
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
</style>
