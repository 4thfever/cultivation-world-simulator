# -*- coding: utf-8 -*-
import pytest
from src.classes.relation.relation import Relation
from src.classes.language import language_manager
from src.i18n import reload_translations, t

def test_relation_i18n_zh_tw():
    # Store original language
    original_lang = str(language_manager)
    print(f"Original lang: {original_lang}")
    
    try:
        # Switch to Traditional Chinese
        language_manager.set_language("zh-TW")
        reload_translations()
        
        print(f"Current lang: {str(language_manager)}")
        
        # Debug: try translating directly
        gp_trans = t("grand_parent")
        print(f"Translation of 'grand_parent': {gp_trans}")
        print(f"Expected: 祖父母")
        
        # Test new relations
        assert str(Relation.GRAND_PARENT) == "祖父母"
        assert str(Relation.GRAND_CHILD) == "孫輩"
        
    finally:
        # Restore original language
        language_manager.set_language(original_lang)
        reload_translations()
