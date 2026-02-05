#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Split messages.po into multiple modules based on comments.
"""

import os
import re
import polib
from pathlib import Path

def get_category_from_comment(comment):
    """
    Extract category from translator comment like "Battle messages"
    Returns lower_case_category_name or None
    """
    if not comment:
        return None
    
    content = ""
    lines = comment.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Polib usually strips the '# ' prefix for tcomment
        # But we handle both cases just to be safe
        if line.startswith('#'):
            content = line.lstrip('#').strip()
        else:
            content = line.strip()

        if not content:
            continue
            
        # Priority Keyword Matching
        # This handles cases like "Battle messages", "Battle - action", "Action: Attack"
        # Also handles "Effect 系统" (Effect System) which contains Chinese characters
        keywords = {
            'Battle': 'battle',
            'Fortune': 'fortune',
            'Misfortune': 'misfortune',
            'MutualAction': 'mutual_action', # Must be before 'Action'
            'Action': 'action',
            'Effect': 'effect',
            'Avatar': 'avatar',
            'Gathering': 'gathering',
            'Cultivation': 'cultivation',
            'Technique': 'technique',
            'Weapon': 'weapon',
            'Auxiliary': 'auxiliary',
            'Elixir': 'elixir',
            'Sect': 'sect',
            'SingleChoice': 'single_choice',
            'Single choice': 'single_choice',
            'Frontend': 'ui',
            'Simulator': 'simulator',
            'Map': 'map',
            'Region': 'map',
            'Relation': 'relation',
            'Root': 'root_element',
            'Appearance': 'appearance',
            'Hidden Domain': 'hidden_domain',
            'Story Styles': 'story_styles',
            'Death reasons': 'death_reasons',
            'Item exchange': 'item_exchange',
            'Alignment': 'alignment',
            'Gender': 'gender',
            'Essence Type': 'essence_type',
            'Realm': 'realm',
            'Stage': 'stage',
            'Direction names': 'direction_names',
            'Feedback labels': 'feedback_labels',
            'Labels': 'labels',
            'LLM Prompt': 'llm_prompt',
            'History': 'history',
        }
        
        for key, val in keywords.items():
            if key in content:
                return val
        
        # If it contains non-ASCII characters and didn't match keywords, dump to misc
        if any(ord(c) > 127 for c in content):
            return 'misc'

        # Fallback: simple snake case for English titles
        # Take the first part before ' - ' or ':'
        parts = re.split(r' [-:] ', content)
        main_part = parts[0].strip()
        
        if len(main_part) < 30 and all(c.isalnum() or c == '_' or c == ' ' for c in main_part):
             return main_part.lower().replace(' ', '_')
             
    return None

def split_po_file(po_path: Path):
    print(f"Processing {po_path}...")
    
    try:
        po = polib.pofile(str(po_path))
    except Exception as e:
        print(f"Error reading {po_path}: {e}")
        return

    # Prepare modules directory
    modules_dir = po_path.parent.parent / "modules"
    
    # Clean up existing modules if any, to avoid left-over garbage files
    if modules_dir.exists():
        for f in modules_dir.glob("*.po"):
            f.unlink()
    else:
        modules_dir.mkdir(exist_ok=True)
    
    # Store entries by category
    categories = {} # category_name -> list[Entry]
    
    current_category = "common"
    
    for entry in po:
        # Try to determine category from translator comment
        new_category = get_category_from_comment(entry.tcomment)
        
        if new_category:
            current_category = new_category
        
        if current_category not in categories:
            categories[current_category] = []
            
        categories[current_category].append(entry)
        
    # Write files
    sorted_cats = sorted(categories.keys())
    print(f"  Split into {len(categories)} categories: {', '.join(sorted_cats)}")
    
    for category in sorted_cats:
        entries = categories[category]
        # Create new PO file with same metadata
        new_po = polib.POFile()
        new_po.metadata = po.metadata
        
        # Copy entries
        for entry in entries:
            new_po.append(entry)
            
        out_path = modules_dir / f"{category}.po"
        new_po.save(str(out_path))
        # print(f"    -> {out_path.name} ({len(entries)} entries)")

def main():
    root_dir = Path("static/locales")
    if not root_dir.exists():
        print(f"Directory not found: {root_dir}")
        return
        
    for lang_dir in root_dir.iterdir():
        if not lang_dir.is_dir() or lang_dir.name == "templates":
            continue
            
        po_file = lang_dir / "LC_MESSAGES" / "messages.po"
        if po_file.exists():
            split_po_file(po_file)
        else:
            print(f"Skipping {lang_dir.name}: messages.po not found")

if __name__ == "__main__":
    main()
