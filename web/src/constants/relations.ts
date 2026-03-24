export const BloodRelationType = {
  TO_ME_IS_PARENT: 'parent',
  TO_ME_IS_CHILD: 'child',
  TO_ME_IS_SIBLING: 'sibling',
  TO_ME_IS_KIN: 'kin',
} as const;

export const IdentityRelationType = {
  TO_ME_IS_MASTER: 'master',
  TO_ME_IS_DISCIPLE: 'apprentice',
  TO_ME_IS_LOVER: 'lovers',
  TO_ME_IS_SWORN_SIBLING: 'sworn_sibling',
} as const;

export const NumericRelationType = {
  ARCHENEMY: 'archenemy',
  DISLIKED: 'disliked',
  STRANGER: 'stranger',
  FRIEND: 'friend',
  BEST_FRIEND: 'best_friend',
} as const;

export type BloodRelationType = typeof BloodRelationType[keyof typeof BloodRelationType];
export type IdentityRelationType = typeof IdentityRelationType[keyof typeof IdentityRelationType];
export type NumericRelationType = typeof NumericRelationType[keyof typeof NumericRelationType];
