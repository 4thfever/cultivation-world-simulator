from enum import Enum

class Month(Enum):
    JANUARY = 1
    FEBRUARY = 2
    MARCH = 3
    APRIL = 4
    MAY = 5
    JUNE = 6
    JULY = 7
    AUGUST = 8
    SEPTEMBER = 9
    OCTOBER = 10
    NOVEMBER = 11
    DECEMBER = 12

    def __str__(self) -> str:
        return str(self.value) 

    def __repr__(self) -> str:
        return str(self.value) 

class Year(int):
    def __add__(self, other: int) -> 'Year':
        return Year(int(self) + other)

def next_month(month: Month, year: Year) -> tuple[Month, Year]:
    if month == Month.DECEMBER:
        return Month.JANUARY, year + 1
    else:
        return Month(month.value + 1), year