def wrap_text(text: str, max_width: int = 20) -> list[str]:
    """
    将长文本按指定宽度换行
    
    Args:
        text: 要换行的文本
        max_width: 每行的最大字符数，默认20
        
    Returns:
        换行后的文本行列表
    """
    if not text:
        return []
    
    lines = []
    current_line = ""
    
    # 按换行符分割，处理已有的换行
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue
            
        words = paragraph.split()
        
        for word in words:
            # 如果当前行加上新词会超过限制
            if len(current_line) + len(word) + 1 > max_width:
                if current_line:
                    lines.append(current_line.strip())
                    current_line = word
                else:
                    # 如果单个词就超过限制，强制换行
                    if len(word) > max_width:
                        # 长词强制切分
                        for i in range(0, len(word), max_width):
                            lines.append(word[i:i + max_width])
                    else:
                        lines.append(word)
            else:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
        
        # 处理段落的最后一行
        if current_line:
            lines.append(current_line.strip())
            current_line = ""
    
    return lines
