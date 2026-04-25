import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMessage } from 'naive-ui'
import { RelationType } from '@/constants/relations'
import { avatarApi } from '@/api'
import type { CreateAvatarParams, GameDataDTO, SimpleAvatarDTO } from '@/types/api'
import { useWorldStore } from '@/stores/world'
import { getAvatarPortraitUrl } from '@/utils/assetUrls'
import { formatEntityGrade } from '@/utils/cultivationText'

export const GENDER_MALE = '男'
export const GENDER_FEMALE = '女'

const createDefaultForm = (): CreateAvatarParams => ({
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
  relations: [],
})

export function useCreateAvatarPanel(onCreated: () => void) {
  const { t } = useI18n()
  const worldStore = useWorldStore()
  const message = useMessage()
  const loading = ref(false)
  const gameData = ref<GameDataDTO | null>(null)
  const avatarMeta = ref<{ males: number[]; females: number[] } | null>(null)
  const avatarList = ref<SimpleAvatarDTO[]>([])
  const createForm = ref<CreateAvatarParams>(createDefaultForm())

  function uiKey(path: string): string {
    return `ui.create_avatar.${path}`
  }

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

  const sectOptions = computed(() => gameData.value?.sects.map(sect => ({
    label: sect.name,
    value: sect.id,
  })) ?? [])

  const personaOptions = computed(() => gameData.value?.personas.map(persona => ({
    label: `${persona.name} (${persona.desc})`,
    value: persona.id,
  })) ?? [])

  const realmOptions = computed(() => gameData.value?.realms.map((realm, index) => ({
    label: t(`realms.${realm}`),
    value: index * 30 + 1,
  })) ?? [])

  const techniqueOptions = computed(() => gameData.value?.techniques.map(item => ({
    label: `${item.name}（${t(`attributes.${item.attribute}`)}·${t(`technique_grades.${item.grade}`)}）`,
    value: item.id,
  })) ?? [])

  const weaponOptions = computed(() => gameData.value?.weapons.map(weapon => ({
    label: `${weapon.name}（${t(`game.info_panel.popup.types.${weapon.type}`)}·${formatEntityGrade(weapon.grade, t)}）`,
    value: weapon.id,
  })) ?? [])

  const auxiliaryOptions = computed(() => gameData.value?.auxiliaries.map(auxiliary => ({
    label: `${auxiliary.name}（${formatEntityGrade(auxiliary.grade, t)}）`,
    value: auxiliary.id,
  })) ?? [])

  const alignmentOptions = computed(() => gameData.value?.alignments.map(alignment => ({
    label: alignment.label,
    value: alignment.value,
  })) ?? [])

  const availableAvatars = computed(() => {
    if (!avatarMeta.value) return []
    const key = createForm.value.gender === GENDER_FEMALE ? 'females' : 'males'
    return avatarMeta.value[key] || []
  })

  const currentAvatarUrl = computed(() => (
    getAvatarPortraitUrl(createForm.value.gender, createForm.value.pic_id)
  ))

  const avatarOptions = computed(() => avatarList.value.map(avatar => ({
    label: `[${avatar.sect_name}] ${avatar.name}`,
    value: avatar.id,
  })))

  async function fetchData() {
    loading.value = true
    try {
      if (!gameData.value) {
        gameData.value = await avatarApi.fetchGameData()
      }
      if (!avatarMeta.value) {
        avatarMeta.value = await avatarApi.fetchAvatarMeta()
      }
      avatarList.value = await avatarApi.fetchAvatarList()
    } catch {
      message.error(t(uiKey('fetch_failed')))
    } finally {
      loading.value = false
    }
  }

  function addRelation() {
    if (!createForm.value.relations) {
      createForm.value.relations = []
    }
    createForm.value.relations.push({
      target_id: '',
      relation: RelationType.TO_ME_IS_FRIEND,
    })
  }

  function removeRelation(index: number) {
    createForm.value.relations?.splice(index, 1)
  }

  async function handleCreateAvatar() {
    if (!createForm.value.level && realmOptions.value.length > 0) {
      createForm.value.level = realmOptions.value[0].value
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
      createForm.value = {
        ...createDefaultForm(),
        level: realmOptions.value[0]?.value,
      }
      onCreated()
    } catch (error) {
      message.error(t(uiKey('create_failed'), { error: String(error) }))
    } finally {
      loading.value = false
    }
  }

  watch(
    () => createForm.value.gender,
    () => {
      createForm.value.pic_id = undefined
    },
  )

  watch(
    realmOptions,
    options => {
      if (!createForm.value.level && options.length > 0) {
        createForm.value.level = options[0].value
      }
    },
    { immediate: true },
  )

  onMounted(() => {
    void fetchData()
  })

  return {
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
    fetchData,
    addRelation,
    removeRelation,
    handleCreateAvatar,
    getAvatarPortraitUrl,
  }
}
