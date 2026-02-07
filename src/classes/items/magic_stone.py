

from typing import Union

class MagicStone(int):
    """
    灵石，实际上是一个int类，代表持有的灵石的数量。
    """
    def __init__(self, value: int):
        self.value = value

    def __str__(self) -> str:
        from src.i18n import t
        return t("{value} Spirit Stones", value=self.value)

    def get_info(self) -> str:
        return str(self)

    def get_detailed_info(self) -> str:
        return str(self)

    def __add__(self, other: Union['MagicStone', int]) -> 'MagicStone':
        if isinstance(other, int):
            return MagicStone(self.value + other)
        return MagicStone(self.value + other.value)

    def __iadd__(self, other: Union['MagicStone', int]) -> 'MagicStone':
        if isinstance(other, int):
            self.value += other
        else:
            self.value += other.value
        return self

    def __sub__(self, other: Union['MagicStone', int]) -> 'MagicStone':
        if isinstance(other, int):
            return MagicStone(self.value - other)
        return MagicStone(self.value - other.value)

    def __isub__(self, other: Union['MagicStone', int]) -> 'MagicStone':
        if isinstance(other, int):
            self.value -= other
        else:
            self.value -= other.value
        return self