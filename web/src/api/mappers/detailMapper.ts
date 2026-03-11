import type { DetailResponseDTO } from '@/types/api';
import type { AvatarDetail, RegionDetail, SectDetail } from '@/types/core';
import type { SelectionType } from '@/stores/ui';

/**
 * 将 /api/detail 返回的 DTO 归一化为前端领域模型。
 *
 * 当前后端已经直接返回接近领域结构的对象，因此这里主要负责：
 * - 根据调用方的 target.type 缩小联合类型
 * - 保留未来在此处做兼容映射的扩展点
 */
export function mapDetailDTOToDomain(
  dto: DetailResponseDTO,
  targetType: SelectionType,
): AvatarDetail | RegionDetail | SectDetail {
  if (targetType === 'avatar') {
    return dto as AvatarDetail;
  }

  if (targetType === 'region') {
    return dto as RegionDetail;
  }

  // 默认为宗门详情
  return dto as SectDetail;
}

