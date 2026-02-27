export const GAME_PHASES = {
  MAP_READY: ['initializing_sects', 'generating_avatars', 'checking_llm', 'generating_initial_events'],
  AVATAR_READY: ['checking_llm', 'generating_initial_events'],
  TEXTURES_READY: ['checking_llm', 'generating_initial_events'],
} as const;
