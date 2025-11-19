import re
from typing import Optional

def wrap_text_by_pixels(font, text: str, max_width_px: int, first_line_max_width_px: Optional[int] = None) -> list[str]:
    """
    使用像素宽度对文本进行自动换行（Word Wrap）。
    支持 <color:R,G,B>...</color> 标签，确保换行时不破坏标签结构。
    
    Args:
        font: 具有 .size(text) -> (w, h) 方法的对象 (如 pygame.font.Font)
        text: 输入文本
        max_width_px: 标准行的最大像素宽度
        first_line_max_width_px: (可选) 第一行的最大像素宽度。用于处理首行缩进或前缀的情况。
                                 如果未提供，默认为 max_width_px。
    
    Returns:
        list[str]: 换行后的文本列表，每行都是独立的富文本字符串
    """
    if not text:
        return []

    normalized_text = text.replace('\\n', '\n')
    paragraphs = normalized_text.split('\n')
    
    wrapped_lines = []
    
    # 标记是否处于整个文本的第一行（用于 first_line_max_width_px）
    is_absolute_first_line = True

    # 匹配颜色标签的正则: 开头标签，或结束标签
    tag_pattern = re.compile(r'(<color:\d+,\d+,\d+>)|(</color>)')

    for paragraph in paragraphs:
        if not paragraph:
            wrapped_lines.append("")
            # 空行也算作一行，之后的行不再是 absolute_first_line
            is_absolute_first_line = False
            continue

        # Tokenize logic including tags
        parts = tag_pattern.split(paragraph)
        raw_tokens = [p for p in parts if p]

        tokens = []
        for rt in raw_tokens:
            if tag_pattern.match(rt):
                tokens.append({'type': 'tag', 'content': rt})
            else:
                current_word = ""
                for char in rt:
                    if char.isascii() and not char.isspace():
                        current_word += char
                    else:
                        if current_word:
                            tokens.append({'type': 'text', 'content': current_word})
                            current_word = ""
                        tokens.append({'type': 'text', 'content': char})
                if current_word:
                    tokens.append({'type': 'text', 'content': current_word})

        # Layout
        current_line_str = ""
        current_width = 0
        active_color_tag = None 

        for token in tokens:
            if token['type'] == 'tag':
                tag_content = token['content']
                current_line_str += tag_content
                if tag_content.startswith('<color'):
                    active_color_tag = tag_content
                else:
                    active_color_tag = None
            else:
                # Text token
                word = token['content']
                w, _ = font.size(word)
                
                # Determine current limit
                current_limit = first_line_max_width_px if (is_absolute_first_line and first_line_max_width_px is not None) else max_width_px
                
                if current_width + w <= current_limit:
                    current_line_str += word
                    current_width += w
                else:
                    # Need to wrap
                    if active_color_tag:
                        current_line_str += "</color>"
                    
                    if current_line_str:
                        wrapped_lines.append(current_line_str)
                        # 发生换行，下一行肯定不是第一行了
                        is_absolute_first_line = False
                    
                    # Start new line
                    current_line_str = ""
                    current_width = 0
                    if active_color_tag:
                        current_line_str += active_color_tag
                    
                    # Check limit again for the new line (which is definitely not first line)
                    # Note: is_absolute_first_line is already False above
                    line_limit = max_width_px
                    
                    if w > line_limit:
                        # Super long word handling
                        temp_word = word
                        while True:
                             w_temp, _ = font.size(temp_word)
                             # Ensure we use the correct limit for the chunk
                             # If we just wrapped, we are on a new line, so use max_width_px
                             current_chunk_limit = max_width_px 
                             
                             if w_temp <= current_chunk_limit:
                                 # Remaining part fits
                                 current_line_str += temp_word
                                 current_width += w_temp
                                 break
                             
                             # Find cut index
                             cut_idx = 1
                             while cut_idx <= len(temp_word):
                                 sub = temp_word[:cut_idx]
                                 sw, _ = font.size(sub)
                                 if sw > current_chunk_limit:
                                     break
                                 cut_idx += 1
                             cut_idx -= 1
                             if cut_idx == 0: cut_idx = 1
                             
                             chunk = temp_word[:cut_idx]
                             current_line_str += chunk
                             if active_color_tag:
                                 current_line_str += "</color>"
                             wrapped_lines.append(current_line_str)
                             is_absolute_first_line = False
                             
                             temp_word = temp_word[cut_idx:]
                             current_line_str = ""
                             if active_color_tag:
                                 current_line_str += active_color_tag
                                 current_width = 0
                    else:
                        if word.isspace():
                            pass
                        else:
                            current_line_str += word
                            current_width += w

        if current_line_str:
            wrapped_lines.append(current_line_str)
            is_absolute_first_line = False

    return wrapped_lines
