

from typing import Union

class MagicStone(int):
    """
    灵石，实际上是一个int类，代表持有的下品灵石的数量。
    但是可以转换为中品、上品灵石。汇率为100:1
    """
    def __init__(self, value: int):
        self.value = value

    def exchange(self) -> tuple[int, int, int]:
        _value, _upper = divmod(self.value, 100)
        _value, _middle = divmod(_value, 100)
        return _upper, _middle, _value

    def __str__(self) -> str:
        _upper, _middle, _value = self.exchange()
        return f"上品灵石：{_upper}，中品灵石：{_middle}，下品灵石：{_value}"

    def __add__(self, other: Union['MagicStone', int]) -> 'MagicStone':
        if isinstance(other, int):
            return MagicStone(self.value + other)
        return MagicStone(self.value + other.value)

    def __sub__(self, other: Union['MagicStone', int]) -> 'MagicStone':
        if isinstance(other, int):
            return MagicStone(self.value - other)
        return MagicStone(self.value - other.value)