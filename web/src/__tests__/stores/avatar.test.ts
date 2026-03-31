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
})
