import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from src.classes.action.respire import Respire
from src.classes.action.meditate import Meditate
from src.classes.action.temper import Temper
from src.classes.action.educate import Educate
from src.classes.action.govern import Govern
from src.classes.action.devour_people import DevourPeople
from src.classes.action.plunder_people import PlunderPeople
from src.classes.action.help_people import HelpPeople
from src.classes.action.catch import Catch
from src.classes.action.sect_mission import SectMission
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar

def test_respire_can_possibly_start(dummy_avatar, base_world):
    action = Respire(dummy_avatar, base_world)
    
    with patch.object(Avatar, 'effects', new_callable=PropertyMock) as mock_effects:
        # Empty legal_actions -> True
        mock_effects.return_value = {}
        assert action.can_possibly_start() is True
        
        # legal_actions contains Respire -> True
        mock_effects.return_value = {"legal_actions": ["Respire"]}
        assert action.can_possibly_start() is True
        
        # legal_actions not empty and doesn't contain Respire -> False
        mock_effects.return_value = {"legal_actions": ["Meditate"]}
        assert action.can_possibly_start() is False

def test_meditate_can_possibly_start(dummy_avatar, base_world):
    action = Meditate(dummy_avatar, base_world)
    
    with patch.object(Avatar, 'effects', new_callable=PropertyMock) as mock_effects:
        # Empty legal_actions -> False
        mock_effects.return_value = {}
        assert action.can_possibly_start() is False
        
        # legal_actions contains Meditate -> True
        mock_effects.return_value = {"legal_actions": ["Meditate"]}
        assert action.can_possibly_start() is True
        
        # legal_actions contains something else -> False
        mock_effects.return_value = {"legal_actions": ["Respire"]}
        assert action.can_possibly_start() is False

def test_temper_can_possibly_start(dummy_avatar, base_world):
    action = Temper(dummy_avatar, base_world)
    
    with patch.object(Avatar, 'effects', new_callable=PropertyMock) as mock_effects:
        # Empty legal_actions -> True
        mock_effects.return_value = {}
        assert action.can_possibly_start() is True
        
        # legal_actions contains Temper -> True
        mock_effects.return_value = {"legal_actions": ["Temper"]}
        assert action.can_possibly_start() is True
        
        # legal_actions not empty and doesn't contain Temper -> False
        mock_effects.return_value = {"legal_actions": ["Meditate"]}
        assert action.can_possibly_start() is False

def test_educate_can_possibly_start(dummy_avatar, base_world):
    action = Educate(dummy_avatar, base_world)
    
    with patch.object(Avatar, 'effects', new_callable=PropertyMock) as mock_effects:
        # Empty legal_actions -> False
        mock_effects.return_value = {}
        assert action.can_possibly_start() is False
        
        # legal_actions contains Educate -> True
        mock_effects.return_value = {"legal_actions": ["Educate"]}
        assert action.can_possibly_start() is True

def test_devour_people_can_possibly_start(dummy_avatar, base_world):
    action = DevourPeople(dummy_avatar, base_world)
    
    with patch.object(Avatar, 'effects', new_callable=PropertyMock) as mock_effects:
        # Empty legal_actions -> False
        mock_effects.return_value = {}
        assert action.can_possibly_start() is False
        
        # legal_actions contains DevourPeople -> True
        mock_effects.return_value = {"legal_actions": ["DevourPeople"]}
        assert action.can_possibly_start() is True

def test_govern_can_possibly_start(dummy_avatar, base_world):
    action = Govern(dummy_avatar, base_world)
    assert action.can_possibly_start() is True

def test_plunder_people_can_possibly_start(dummy_avatar, base_world):
    action = PlunderPeople(dummy_avatar, base_world)
    
    dummy_avatar.alignment = Alignment.RIGHTEOUS
    assert action.can_possibly_start() is False
    
    dummy_avatar.alignment = Alignment.NEUTRAL
    assert action.can_possibly_start() is False
    
    dummy_avatar.alignment = Alignment.EVIL
    assert action.can_possibly_start() is True

def test_help_people_can_possibly_start(dummy_avatar, base_world):
    action = HelpPeople(dummy_avatar, base_world)
    
    dummy_avatar.alignment = Alignment.EVIL
    assert action.can_possibly_start() is False
    
    dummy_avatar.alignment = Alignment.NEUTRAL
    assert action.can_possibly_start() is False
    
    dummy_avatar.alignment = Alignment.RIGHTEOUS
    assert action.can_possibly_start() is True

def test_catch_can_possibly_start(dummy_avatar, base_world):
    action = Catch(dummy_avatar, base_world)
    
    # No sect -> False
    dummy_avatar.sect = None
    assert action.can_possibly_start() is False
    
    # Other sect -> False
    mock_sect = MagicMock()
    mock_sect.name = "Other Sect"
    dummy_avatar.sect = mock_sect
    assert action.can_possibly_start() is False
    
    # 百兽宗 -> True
    mock_sect.name = "百兽宗"
    dummy_avatar.sect = mock_sect
    assert action.can_possibly_start() is True

def test_sect_mission_can_possibly_start(dummy_avatar, base_world):
    action = SectMission(dummy_avatar, base_world)

    dummy_avatar.sect = None
    assert action.can_possibly_start() is False

    mock_sect = MagicMock()
    mock_sect.id = 1
    mock_sect.name = "测试宗门"
    mock_sect.members = {}
    dummy_avatar.sect = mock_sect
    assert action.can_possibly_start() is True
