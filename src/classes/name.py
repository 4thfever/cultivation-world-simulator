import random
from typing import Optional, Union
from dataclasses import dataclass

from src.utils.df import game_configs, get_str, get_int
from src.classes.avatar import Gender


@dataclass
class LastName:
    """姓氏"""
    name: str
    sect: Optional[str]
    
@dataclass
class GivenName:
    """名字"""
    name: str
    gender: Gender
    sect: Optional[int]


class NameManager:
    """姓名管理器"""
    
    def __init__(self):
        # 散修通用姓氏
        self.common_last_names: list[str] = []
        # 按宗门分类的姓氏 {宗门名: [姓氏列表]}
        self.sect_last_names: dict[str, list[str]] = {}
        
        # 散修通用名字 {Gender: [名字列表]}
        self.common_given_names: dict[Gender, list[str]] = {
            Gender.MALE: [],
            Gender.FEMALE: []
        }
        # 按宗门和性别分类的名字 {宗门ID: {Gender: [名字列表]}}
        self.sect_given_names: dict[int, dict[Gender, list[str]]] = {}
        
        self._load_names()
    
    def _load_names(self):
        """从CSV加载姓名数据"""
        # 加载姓氏 (保留使用 name 引用)
        last_name_df = game_configs["last_name"]
        for row in last_name_df:
            name = get_str(row, "last_name")
            sect = get_str(row, "sect")
            
            if sect:
                if sect not in self.sect_last_names:
                    self.sect_last_names[sect] = []
                self.sect_last_names[sect].append(name)
            else:
                self.common_last_names.append(name)
        
        # 加载名字 (使用 sect_id 引用)
        given_name_df = game_configs["given_name"]
        for row in given_name_df:
            name = get_str(row, "given_name")
            gender_str = get_str(row, "gender")
            gender = Gender.MALE if gender_str == "男" else Gender.FEMALE
            # 尝试读取 sect_id，兼容旧的 sect 列（虽然已经被迁移脚本改了）
            sect_id = get_int(row, "sect_id")
            
            if sect_id > 0:
                if sect_id not in self.sect_given_names:
                    self.sect_given_names[sect_id] = {Gender.MALE: [], Gender.FEMALE: []}
                self.sect_given_names[sect_id][gender].append(name)
            else:
                self.common_given_names[gender].append(name)
    
    def get_random_last_name(self, sect_name: Optional[str] = None) -> str:
        """
        获取随机姓氏
        """
        if sect_name and sect_name in self.sect_last_names:
            return random.choice(self.sect_last_names[sect_name])
        return random.choice(self.common_last_names)
    
    def get_random_given_name(self, gender: Gender, sect_id: Optional[int] = None) -> str:
        """
        获取随机名字
        """
        if sect_id and sect_id in self.sect_given_names:
            sect_names = self.sect_given_names[sect_id][gender]
            if sect_names:
                return random.choice(sect_names)
        return random.choice(self.common_given_names[gender])
    
    def get_random_full_name(self, gender: Gender, sect_name: Optional[str] = None, sect_id: Optional[int] = None) -> str:
        """
        获取随机全名
        """
        last_name = self.get_random_last_name(sect_name)
        given_name = self.get_random_given_name(gender, sect_id)
        return last_name + given_name
    
    def get_random_full_name_with_surname(
        self, 
        gender: Gender, 
        surname: str, 
        sect_id: Optional[int] = None
    ) -> str:
        """
        使用指定姓氏生成随机全名
        """
        if not surname:
            # 如果没有提供姓氏，回退到随机全名（这里假设没有 sect_name 传进来，因为这个函数签名里没有）
            # 为了严谨，这里只能生成随机名
            return self.get_random_full_name(gender, None, sect_id)
            
        given_name = self.get_random_given_name(gender, sect_id)
        return surname + given_name


# 全局单例
_name_manager = NameManager()


def get_random_name(gender: Gender, sect_name: Optional[str] = None, sect_id: Optional[int] = None) -> str:
    """获取随机全名"""
    return _name_manager.get_random_full_name(gender, sect_name, sect_id)


def get_random_name_for_sect(gender: Gender, sect) -> str:
    """
    基于宗门生成姓名（兼容旧接口）
    """
    sect_name = sect.name if sect is not None else None
    sect_id = sect.id if sect is not None else None
    return _name_manager.get_random_full_name(gender, sect_name, sect_id)


def pick_surname_for_sect(sect) -> str:
    """
    从宗门常见姓或全局库中挑选一个姓氏（兼容旧接口）
    """
    sect_name = sect.name if sect is not None else None
    return _name_manager.get_random_last_name(sect_name)


def get_random_name_with_surname(
    gender: Gender, 
    surname: str, 
    sect
) -> str:
    """
    使用指定姓氏生成随机全名（兼容旧接口）
    """
    sect_id = sect.id if sect is not None else None
    return _name_manager.get_random_full_name_with_surname(gender, surname, sect_id)
