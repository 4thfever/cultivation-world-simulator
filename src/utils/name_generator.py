import random
from typing import Optional, Union
from dataclasses import dataclass

from src.utils.df import game_configs, get_str, get_int
from src.classes.core.avatar import Gender


@dataclass
class LastName:
    """姓氏"""
    name: str
    sect_id: Optional[int]
    
@dataclass
class GivenName:
    """名字"""
    name: str
    gender: Gender
    sect_id: Optional[int]


class NameManager:
    """姓名管理器"""
    
    def __init__(self):
        # 散修通用姓氏
        self.common_last_names: list[str] = []
        # 按宗门分类的姓氏 {宗门ID: [姓氏列表]}
        self.sect_last_names: dict[int, list[str]] = {}
        
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
        # 清空现有数据
        self.common_last_names.clear()
        self.sect_last_names.clear()
        for g_list in self.common_given_names.values():
            g_list.clear()
        self.sect_given_names.clear()
        
        # 加载姓氏 (不再区分 _en 后缀，因为 config/df 已经处理了加载逻辑)
        last_name_df = game_configs.get("last_name", [])
            
        if last_name_df:
            for row in last_name_df:
                name = get_str(row, "last_name")
                sect_id = get_int(row, "sect_id")
                
                if sect_id > 0:
                    if sect_id not in self.sect_last_names:
                        self.sect_last_names[sect_id] = []
                    self.sect_last_names[sect_id].append(name)
                else:
                    self.common_last_names.append(name)
        
        # 加载名字
        given_name_df = game_configs.get("given_name", [])
            
        if given_name_df:
            for row in given_name_df:
                name = get_str(row, "given_name")
                gender_val = get_int(row, "gender") # 0 or 1
                # 假设 1=Male, 0=Female
                gender = Gender.MALE if gender_val == 1 else Gender.FEMALE
                
                sect_id = get_int(row, "sect_id")
                
                if sect_id > 0:
                    if sect_id not in self.sect_given_names:
                        self.sect_given_names[sect_id] = {Gender.MALE: [], Gender.FEMALE: []}
                    self.sect_given_names[sect_id][gender].append(name)
                else:
                    self.common_given_names[gender].append(name)
    
    def get_random_last_name(self, sect_id: Optional[int] = None) -> str:
        """
        获取随机姓氏
        """
        if sect_id and sect_id in self.sect_last_names:
            return random.choice(self.sect_last_names[sect_id])
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
    
    def get_random_full_name(self, gender: Gender, sect_id: Optional[int] = None) -> str:
        """
        获取随机全名
        """
        last_name = self.get_random_last_name(sect_id)
        given_name = self.get_random_given_name(gender, sect_id)
        
        # 处理 i18n 拼接逻辑
        from src.classes.language import language_manager, LanguageType
        if language_manager.current == LanguageType.EN_US:
            return f"{last_name} {given_name}"
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
            # 如果没有提供姓氏，回退到随机全名
            return self.get_random_full_name(gender, sect_id)
            
        given_name = self.get_random_given_name(gender, sect_id)
        
        # 处理 i18n 拼接逻辑
        from src.classes.language import language_manager, LanguageType
        if language_manager.current == LanguageType.EN_US:
            return f"{surname} {given_name}"
        return surname + given_name


# 全局单例
_name_manager = NameManager()


def get_random_name(gender: Gender, sect_name: Optional[str] = None, sect_id: Optional[int] = None) -> str:
    """获取随机全名"""
    # 兼容性处理：如果只给了 sect_name 没给 sect_id，这里没办法直接转 ID (需要额外映射表)
    # 但调用方应该已经被更新或者只使用 sect 对象
    return _name_manager.get_random_full_name(gender, sect_id)


def get_random_name_for_sect(gender: Gender, sect) -> str:
    """
    基于宗门生成姓名（兼容旧接口）
    """
    sect_id = sect.id if sect is not None else None
    return _name_manager.get_random_full_name(gender, sect_id)


def pick_surname_for_sect(sect) -> str:
    """
    从宗门常见姓或全局库中挑选一个姓氏（兼容旧接口）
    """
    sect_id = sect.id if sect is not None else None
    return _name_manager.get_random_last_name(sect_id)


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


def reload():
    """重新加载数据"""
    _name_manager._load_names()
