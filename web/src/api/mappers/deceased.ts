import type { DeceasedRecordDTO } from '@/types/api'

export interface DeceasedRecordView {
  id: string
  name: string
  gender: string
  ageAtDeath: number
  realmDisplay: string
  stageDisplay: string
  deathReason: string
  deathYear: number
  deathMonth: number
  sectName: string
  alignment: string
  backstory: string | null
  customPicId: number | null
}

export function mapDeceasedRecord(dto: DeceasedRecordDTO): DeceasedRecordView {
  return {
    id: dto.id,
    name: dto.name,
    gender: dto.gender,
    ageAtDeath: dto.age_at_death,
    realmDisplay: dto.realm_at_death,
    stageDisplay: dto.stage_at_death,
    deathReason: dto.death_reason,
    deathYear: Math.floor(dto.death_time / 12) + 1,
    deathMonth: (dto.death_time % 12) + 1,
    sectName: dto.sect_name_at_death,
    alignment: dto.alignment_at_death,
    backstory: dto.backstory,
    customPicId: dto.custom_pic_id,
  }
}

export function mapDeceasedList(dtos: DeceasedRecordDTO[]): DeceasedRecordView[] {
  return dtos.map(mapDeceasedRecord)
}
