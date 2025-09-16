from dataclasses import dataclass

from src.classes.cultivation import Realm

@dataclass
class HP:
    """
    血量。
    会因为战斗，天灾或者其他原因降低cur。
    会随时间或者服用丹药等补充cur。
    会因为突破境界，服用丹药等增加max。
    """
    max: int 
    cur: int 

    def reduce(self, value_2_reduce:int) -> bool:
        self.cur -= value_2_reduce
        is_alive = True
        if self.cur < 0:
            is_alive = False
        return is_alive

    def recover(self, value_2_recover:int) -> bool:
        self.cur += value_2_recover
        if self.cur > self.max:
            self.cur = self.max
        return True

    def add_max(self, value_2_add:int) -> bool:
        self.max += value_2_add
        return True

    def __str__(self) -> str:
        return f"{self.cur}/{self.max}"
    
    def __repr__(self) -> str:
        return self.__str__()
        
HP_MAX_BY_REALM = {
    Realm.Qi_Refinement: 100,
    Realm.Foundation_Establishment: 200,
    Realm.Core_Formation: 300,
    Realm.Nascent_Soul: 400,
}


@dataclass
class MP:
    """
    灵力
    会因为战斗而消耗cur。
    会随时间或者服用丹药等补充cur。
    会因为突破境界，服用丹药等增加max。
    """
    max: int
    cur: int

    def can_cast(self, value_2_cast:int) -> bool:
        return self.cur >= value_2_cast

    def reduce(self, value_2_reduce:int) -> bool:
        self.cur -= value_2_reduce
        if self.cur < 0:
            self.cur = 0
        return True

    def recover(self, value_2_recover:int) -> bool:
        self.cur += value_2_recover
        if self.cur > self.max:
            self.cur = self.max
        return True

    def __str__(self) -> str:
        return f"{self.cur}/{self.max}"
    
    def __repr__(self) -> str:
        return self.__str__()

    def add_max(self, value_2_add:int) -> bool:
        self.max += value_2_add
        return True

MP_MAX_BY_REALM = {
    Realm.Qi_Refinement: 100,
    Realm.Foundation_Establishment: 200,
    Realm.Core_Formation: 300,
    Realm.Nascent_Soul: 400,
}