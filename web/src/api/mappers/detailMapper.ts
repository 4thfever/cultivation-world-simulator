import type { DetailResponseDTO } from '@/types/api';
import type { AvatarDetail, RegionDetail, SectDetail } from '@/types/core';
import type { SelectionType } from '@/stores/ui';

type DetailDomainByType<T extends SelectionType> =
  T extends 'avatar'
    ? AvatarDetail
    : T extends 'region'
      ? RegionDetail
      : SectDetail;

/**
 * 将 /api/v1/query/detail 返回的 DTO 归一化为前端领域模型。
 *
 * 当前后端已经直接返回接近领域结构的对象，因此这里主要负责：
 * - 根据调用方的 target.type 缩小联合类型
 * - 保留未来在此处做兼容映射的扩展点
 */
export function mapDetailDTOToDomain(
  dto: DetailResponseDTO,
  targetType: 'avatar',
): AvatarDetail;
export function mapDetailDTOToDomain(
  dto: DetailResponseDTO,
  targetType: 'region',
): RegionDetail;
export function mapDetailDTOToDomain(
  dto: DetailResponseDTO,
  targetType: 'sect',
): SectDetail;
export function mapDetailDTOToDomain<T extends SelectionType>(
  dto: DetailResponseDTO,
  targetType: T,
): DetailDomainByType<T>;
export function mapDetailDTOToDomain(
  dto: DetailResponseDTO,
  _targetType: SelectionType,
): AvatarDetail | RegionDetail | SectDetail {
  return dto;
}

