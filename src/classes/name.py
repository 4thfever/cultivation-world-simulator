import random
from typing import Optional
from dataclasses import dataclass

from src.utils.df import game_configs, get_str
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
    sect: Optional[str]


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
        # 按宗门和性别分类的名字 {宗门名: {Gender: [名字列表]}}
        self.sect_given_names: dict[str, dict[Gender, list[str]]] = {}
        
        self._load_names()
    
    def _load_names(self):
        """从CSV加载姓名数据"""
        # 加载姓氏
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
        
        # 加载名字
        given_name_df = game_configs["given_name"]
        for row in given_name_df:
            name = get_str(row, "given_name")
            gender_str = get_str(row, "gender")
            gender = Gender.MALE if gender_str == "男" else Gender.FEMALE
            sect = get_str(row, "sect")
            
            if sect:
                if sect not in self.sect_given_names:
                    self.sect_given_names[sect] = {Gender.MALE: [], Gender.FEMALE: []}
                self.sect_given_names[sect][gender].append(name)
            else:
                self.common_given_names[gender].append(name)
    
    def get_random_last_name(self, sect_name: Optional[str] = None) -> str:
        """
        获取随机姓氏
        
        Args:
            sect_name: 宗门名称，如果为None则从散修姓氏中选择
            
        Returns:
            姓氏字符串
        """
        if sect_name and sect_name in self.sect_last_names:
            return random.choice(self.sect_last_names[sect_name])
        return random.choice(self.common_last_names)
    
    def get_random_given_name(self, gender: Gender, sect_name: Optional[str] = None) -> str:
        """
        获取随机名字
        
        Args:
            gender: 性别
            sect_name: 宗门名称，如果为None则从散修名字中选择
            
        Returns:
            名字字符串
        """
        if sect_name and sect_name in self.sect_given_names:
            sect_names = self.sect_given_names[sect_name][gender]
            if sect_names:
                return random.choice(sect_names)
        return random.choice(self.common_given_names[gender])
    
    def get_random_full_name(self, gender: Gender, sect_name: Optional[str] = None) -> str:
        """
        获取随机全名
        
        Args:
            gender: 性别
            sect_name: 宗门名称，如果为None则为散修
            
        Returns:
            完整姓名
        """
        last_name = self.get_random_last_name(sect_name)
        given_name = self.get_random_given_name(gender, sect_name)
        return last_name + given_name
    
    def get_random_full_name_with_surname(
        self, 
        gender: Gender, 
        surname: str, 
        sect_name: Optional[str] = None
    ) -> str:
        """
        使用指定姓氏生成随机全名
        
        Args:
            gender: 性别
            surname: 指定的姓氏
            sect_name: 宗门名称，如果为None则为散修
            
        Returns:
            完整姓名
        """
        if not surname:
            return self.get_random_full_name(gender, sect_name)
        given_name = self.get_random_given_name(gender, sect_name)
        return surname + given_name


# 全局单例
_name_manager = NameManager()


def get_random_name(gender: Gender, sect_name: Optional[str] = None) -> str:
    """获取随机全名"""
    return _name_manager.get_random_full_name(gender, sect_name)


def get_random_name_for_sect(gender: Gender, sect) -> str:
    """
    基于宗门生成姓名（兼容旧接口）
    
    Args:
        gender: 性别
        sect: Sect对象或None
        
    Returns:
        完整姓名
    """
    sect_name = sect.name if sect is not None else None
    return _name_manager.get_random_full_name(gender, sect_name)


def pick_surname_for_sect(sect) -> str:
    """
    从宗门常见姓或全局库中挑选一个姓氏（兼容旧接口）
    
    Args:
        sect: Sect对象或None
        
    Returns:
        姓氏
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
    
    Args:
        gender: 性别
        surname: 指定的姓氏
        sect: Sect对象或None
        
    Returns:
        完整姓名
    """
    sect_name = sect.name if sect is not None else None
    return _name_manager.get_random_full_name_with_surname(gender, surname, sect_name)
