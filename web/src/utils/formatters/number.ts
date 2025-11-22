/**
 * 格式化工具
 */

export function formatNumber(num: number): string {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万';
  }
  return num.toString();
}

export function formatHp(current: number, max: number): string {
  return `${Math.floor(current)} / ${max}`;
}

export function formatAge(age: number, lifespan: number): string {
  return `${age} / ${lifespan}`;
}

