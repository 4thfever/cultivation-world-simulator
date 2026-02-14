/**
 * 关系类型常量
 * 用于描述“对方是我的谁” (Target is My ...)
 * 
 * 对应后端 src/classes/relation/relation.py 中的 Relation 枚举
 * 
 * 防呆提示：
 * 这里的主语是【对方/Target】，宾语是【我/Me】。
 * 例如：TO_ME_IS_PARENT 意味着 "Target is Parent of Me" (对方是我的父母)
 */
export const RelationType = {
  // —— 血缘 (Innate) ——
  // 对方是我的父/母 (后端: IS_PARENT_OF / "parent")
  TO_ME_IS_PARENT: 'parent',
  // 对方是我的子/女 (后端: IS_CHILD_OF / "child")
  TO_ME_IS_CHILD: 'child',
  // 对方是我的兄弟姐妹 (后端: IS_SIBLING_OF / "sibling")
  TO_ME_IS_SIBLING: 'sibling',

  // —— 社会 (Social) ——
  // 对方是我的师傅 (后端: IS_MASTER_OF / "master")
  TO_ME_IS_MASTER: 'master',
  // 对方是我的徒弟 (后端: IS_DISCIPLE_OF / "apprentice")
  TO_ME_IS_DISCIPLE: 'apprentice',
  
  // —— 对称关系 (Symmetric) ——
  // 对方是我的道侣 (后端: IS_LOVER_OF / "lovers")
  TO_ME_IS_LOVER: 'lovers',
  // 对方是我的朋友 (后端: IS_FRIEND_OF / "friend")
  TO_ME_IS_FRIEND: 'friend',
  // 对方是我的仇人 (后端: IS_ENEMY_OF / "enemy")
  TO_ME_IS_ENEMY: 'enemy'
} as const;

export type RelationType = typeof RelationType[keyof typeof RelationType];
