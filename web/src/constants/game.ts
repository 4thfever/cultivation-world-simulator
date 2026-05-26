export const GAME_PHASES = {
  MAP_READY: ['initializing_sects', 'generating_avatars', 'preparing_character_profiles', 'generating_initial_events'],
  AVATAR_READY: ['preparing_character_profiles', 'generating_initial_events'],
  TEXTURES_READY: ['preparing_character_profiles', 'generating_initial_events'],
} as const;
