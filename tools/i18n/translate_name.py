import csv
import os
from pypinyin import pinyin, Style

def translate_names():
    # 获取当前脚本所在目录的父目录的父目录，即项目根目录
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    zh_dir = os.path.join(base_dir, "static", "locales", "zh-CN", "game_configs")
    en_dir = os.path.join(base_dir, "static", "locales", "en-US", "game_configs")
    
    if not os.path.exists(en_dir):
        os.makedirs(en_dir, exist_ok=True)
    
    files = ["last_name.csv", "given_name.csv"]
    
    for filename in files:
        zh_path = os.path.join(zh_dir, filename)
        en_path = os.path.join(en_dir, filename)
        
        if not os.path.exists(zh_path):
            print(f"Warning: {zh_path} does not exist.")
            continue
            
        rows = []
        with open(zh_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
                desc = next(reader)
            except StopIteration:
                continue
            
            # 读取所有行
            original_rows = list(reader)

        # 处理表头翻译 (虽然列名是英文，但为了统一，可以这里显式定义，或者直接复用)
        # last_name.csv: last_name, sect_id, cond
        # given_name.csv: given_name, gender, sect_id, cond
        
        # 描述行翻译
        en_desc = []
        if filename == "last_name.csv":
            en_desc = ["Surname", "Sect ID", "Condition"]
        elif filename == "given_name.csv":
            en_desc = ["Given Name", "Gender(0=Female,1=Male)", "Sect ID", "Condition"]
        else:
            en_desc = desc # Fallback
            
        for row in original_rows:
            if not row or not row[0]:
                if row:
                    rows.append(row)
                continue
            
            # 第一列是姓名
            chinese_name = row[0]
            # 转换为拼音，Style.NORMAL 表示不带声调
            py_list = pinyin(chinese_name, style=Style.NORMAL)
            # 拼接，首字母大写，其余小写，例如 "si", "ma" -> "Sima"
            py_name = "".join([p[0] for p in py_list]).capitalize()
            
            new_row = [py_name] + row[1:]
            rows.append(new_row)
            
        with open(en_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header) # Header key unchanged
            writer.writerow(en_desc) # Use English desc
            writer.writerows(rows)
        
        print(f"Successfully translated {filename} to {en_path}")

if __name__ == "__main__":
    translate_names()
