import math

def chebyshev_distance(p1: tuple[int, int], p2: tuple[int, int]) -> int:
    """
    计算切比雪夫距离：max(|x1-x2|, |y1-y2|)
    适用于允许对角线移动的网格地图
    """
    return max(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))

def manhattan_distance(p1: tuple[int, int], p2: tuple[int, int]) -> int:
    """
    计算曼哈顿距离：|x1-x2| + |y1-y2|
    适用于只允许四向移动的网格地图
    """
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def euclidean_distance(p1: tuple[int, int], p2: tuple[int, int]) -> float:
    """
    计算欧几里得距离：sqrt((x1-x2)^2 + (y1-y2)^2)
    """
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

