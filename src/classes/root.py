"""
灵根
目前只有五行灵根，金木水火土。
"""

from enum import Enum


class Root(Enum):
    """
    灵根
    """
    Metal = "金"
    Wood = "木"
    Water = "水"
    Fire = "火"
    Earth = "土"