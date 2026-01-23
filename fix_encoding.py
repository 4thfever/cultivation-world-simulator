
import os

def fix_po_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Try to decode as utf-8
        try:
            text = content.decode('utf-8')
            print(f"{filepath} is valid utf-8.")
        except UnicodeDecodeError:
            print(f"{filepath} is NOT valid utf-8. Attempting to fix...")
            # It's likely the appended part is in a different encoding (e.g. GBK/CP936 since I am on Windows CN)
            # The original part was UTF-8.
            # Let's try to decode the last part with GBK if possible, or just load everything as 'latin1' or 'gbk' and save as utf-8.
            # However, mixing encodings is tricky.
            # Best bet: The original file was UTF-8. The appended part was likely written by PowerShell's Add-Content which might use UTF-16 or ANSI (GBK).
            
            # Let's try to find where the corruption starts.
            # We know the original file ended before my append.
            # But simpler: read as binary, look for non-utf8 sequences at the end.
            
            # Alternative: Read with 'errors="replace"' and save as utf-8.
            text = content.decode('utf-8', errors='replace')
            
            # Check if we have replacement characters at the end
            # If so, maybe we can recover the text if we know what it was.
            # I know what I appended.
            
            # Actually, I can just truncate the file to the last valid known point and append correctly.
            # But easier: I know what I added. I can just search for the start of my additions and replace them.
            
            # Let's just write back the text as utf-8. The 'replace' might have lost data, but let's see.
            pass

    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    # To be safe, let's strip the last few lines (my additions) and re-add them properly.
    lines = text.splitlines()
    
    # Remove lines after the last known good line if they look suspicious or just remove my added keys to be safe
    # My added keys start with: msgid "(Alignment: {alignment}
    
    clean_lines = []
    found_append_start = False
    for line in lines:
        if 'msgid "(Alignment: {alignment}' in line:
            found_append_start = True
            break
        clean_lines.append(line)
    
    if found_append_start:
        print("Found appended section, stripping it.")
    else:
        print("Did not find appended section start, maybe it's corrupted or I missed it.")
        # If I can't find it, maybe the corruption prevents string matching?
        # But decode with replace should produce a string.
        pass

    content_str = '\n'.join(clean_lines) + '\n'
    
    # Re-append the correct content
    if 'zh_CN' in filepath:
        append_content = """
msgid "(Alignment: {alignment}, Style: {style}, Headquarters: {hq_name}){effect}"
msgstr "（阵营：{alignment}，风格：{style}，驻地：{hq_name}）{effect}"

msgid "Drops: {materials}"
msgstr "掉落：{materials}"

msgid "[{name}] ({realm})"
msgstr "【{name}】（{realm}）"

msgid "{name} ({attribute}) {grade}"
msgstr "{name}（{attribute}）{grade}"

msgid "{name} ({attribute}) {grade} {desc}{effect}"
msgstr "{name}（{attribute}）{grade} {desc}{effect}"

msgid "{name} ({attribute}·{grade})"
msgstr "{name}（{attribute}·{grade}）"

msgid "{name} ({type}·{realm}, {desc}){effect}"
msgstr "{name}（{type}·{realm}，{desc}）{effect}"
"""
    else:
        append_content = """
msgid "(Alignment: {alignment}, Style: {style}, Headquarters: {hq_name}){effect}"
msgstr "(Alignment: {alignment}, Style: {style}, Headquarters: {hq_name}){effect}"

msgid "Drops: {materials}"
msgstr "Drops: {materials}"

msgid "[{name}] ({realm})"
msgstr "[{name}] ({realm})"

msgid "{name} ({attribute}) {grade}"
msgstr "{name} ({attribute}) {grade}"

msgid "{name} ({attribute}) {grade} {desc}{effect}"
msgstr "{name} ({attribute}) {grade} {desc}{effect}"

msgid "{name} ({attribute}·{grade})"
msgstr "{name} ({attribute}·{grade})"

msgid "{name} ({type}·{realm}, {desc}){effect}"
msgstr "{name} ({type}·{realm}, {desc}){effect}"
"""

    full_content = content_str + append_content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(full_content)
    print(f"Fixed {filepath}")

fix_po_file('src/i18n/locales/zh_CN/LC_MESSAGES/messages.po')
fix_po_file('src/i18n/locales/en_US/LC_MESSAGES/messages.po')
