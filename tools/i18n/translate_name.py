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
            
        with open(zh_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
                desc = next(reader)
            except StopIteration:
                continue
            
            rows = list(reader)
            
        with open(en_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow(desc)
            
            for row in rows:
                if not row or not row[0]:
                    if row:
                        writer.writerow(row)
                    continue
                
                # 第一列是姓名
                chinese_name = row[0]
                # 转换为拼音，Style.NORMAL 表示不带声调
                py_list = pinyin(chinese_name, style=Style.NORMAL)
                # 拼接并首字母大写，例如 "si", "ma" -> "Sima"
                py_name = "".join([p[0].capitalize() for p in py_list])
                
                new_row = [py_name] + row[1:]
                writer.writerow(new_row)
        
        print(f"Successfully translated {filename} to {en_path}")

if __name__ == "__main__":
    translate_names()
