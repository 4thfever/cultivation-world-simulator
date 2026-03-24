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

// Backward-compatible aggregate used by older panels such as CreateAvatarPanel.
// Keep friend/enemy mapped to relation payload values accepted by the backend.
export const RelationType = {
  TO_ME_IS_PARENT: BloodRelationType.TO_ME_IS_PARENT,
  TO_ME_IS_CHILD: BloodRelationType.TO_ME_IS_CHILD,
  TO_ME_IS_SIBLING: BloodRelationType.TO_ME_IS_SIBLING,
  TO_ME_IS_KIN: BloodRelationType.TO_ME_IS_KIN,
  TO_ME_IS_MASTER: IdentityRelationType.TO_ME_IS_MASTER,
  TO_ME_IS_DISCIPLE: IdentityRelationType.TO_ME_IS_DISCIPLE,
  TO_ME_IS_LOVER: IdentityRelationType.TO_ME_IS_LOVER,
  TO_ME_IS_SWORN_SIBLING: IdentityRelationType.TO_ME_IS_SWORN_SIBLING,
  TO_ME_IS_FRIEND: NumericRelationType.FRIEND,
  TO_ME_IS_ENEMY: 'enemy',
} as const;

export type BloodRelationType = typeof BloodRelationType[keyof typeof BloodRelationType];
export type IdentityRelationType = typeof IdentityRelationType[keyof typeof IdentityRelationType];
export type NumericRelationType = typeof NumericRelationType[keyof typeof NumericRelationType];
export type RelationType = typeof RelationType[keyof typeof RelationType];
