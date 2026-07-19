import { describe, expect, it } from 'vitest'
import { useAvatarStore } from '@/stores/avatar'

describe('useAvatarStore', () => {
  it('updates a single avatar summary without replacing unrelated fields', () => {
    const store = useAvatarStore()

    store.updateAvatars([
      {
        id: 'avatar-1',
        name: 'Test Avatar',
        x: 3,
        y: 4,
        gender: 'male',
        pic_id: 2,
      },
    ])

    store.updateAvatarSummary('avatar-1', { pic_id: 9 })

    expect(store.avatars.get('avatar-1')).toEqual({
      id: 'avatar-1',
      name: 'Test Avatar',
      x: 3,
      y: 4,
      gender: 'male',
      pic_id: 9,
    })
  })

  it('removes an avatar summary by id', () => {
    const store = useAvatarStore()

    store.updateAvatars([
      {
        id: 'avatar-1',
        name: 'Test Avatar',
        x: 3,
        y: 4,
        gender: 'male',
      },
      {
        id: 'avatar-2',
        name: 'Other Avatar',
        x: 8,
        y: 9,
        gender: 'female',
      },
    ])

    store.removeAvatar('avatar-1')

    expect(store.avatars.has('avatar-1')).toBe(false)
    expect(store.avatars.has('avatar-2')).toBe(true)
  })
})
