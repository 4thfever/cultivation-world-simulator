import asyncio
import json
import argparse
import csv
from pathlib import Path
from typing import Dict, List, Any
import sys

# Add project root to python path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.utils.llm import call_llm_json
from src.utils.io import read_txt

CHUNK_SIZE = 12000
CSV_OUTPUT_PATH = project_root / "tools" / "extract" / "res.csv"

PROMPT_TEMPLATE = """
你是一位修仙小说分析专家。
请从以下文本中提取所有与“宗门”相关的信息。
对于找到的每个宗门，请提取以下内容：
- 宗门名称 (作为 JSON 的 key)
- 行事风格 (Style)
- 总部 (Headquarters)
- 成员 (Members)
- 功法 (Techniques)
- 宝物 (Treasures)

请以 JSON 格式返回结果：
{
  "宗门名称": {
    "行事风格": "描述...",
    "总部": "描述...",
    "成员": ["成员1", "成员2"],
    "功法": ["功法1", "功法2"],
    "宝物": ["宝物1"]
  }
}

如果未找到任何宗门信息，请返回空 JSON {}。
如果找到的宗门信息不全，只记录找到的部分，其他的部分留空str或者空list。千万不要自己编造。
确保返回的是合法的 JSON 格式。

文本片段：
{text_chunk}
"""

def split_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split text into chunks of approximately chunk_size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

async def process_chunk(chunk: str, index: int, total: int) -> Dict[str, Any]:
    """Process a single chunk using LLM."""
    print(f"Processing chunk {index + 1}/{total}...")
    prompt = PROMPT_TEMPLATE.replace("{text_chunk}", chunk)
    try:
        # Using a high retry count as per user request (implied reliability)
        # But call_llm_json already has retries.
        result = await call_llm_json(prompt)
        return result
    except Exception as e:
        print(f"Error processing chunk {index + 1}: {e}")
        return {}

def merge_results(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge results from multiple chunks."""
    final_data = {}
    
    for result in all_results:
        if not result:
            continue
            
        for sect_name, data in result.items():
            if sect_name not in final_data:
                final_data[sect_name] = {
                    "行事风格": data.get("行事风格", ""),
                    "总部": data.get("总部", ""),
                    "成员": data.get("成员", []) if isinstance(data.get("成员"), list) else [],
                    "功法": data.get("功法", []) if isinstance(data.get("功法"), list) else [],
                    "宝物": data.get("宝物", []) if isinstance(data.get("宝物"), list) else [],
                }
            else:
                existing = final_data[sect_name]
                
                # Merge text fields (append if different and not empty)
                for key in ["行事风格", "总部"]:
                    new_val = data.get(key, "")
                    if new_val and new_val not in existing[key]:
                        if existing[key]:
                            existing[key] += " | " + new_val
                        else:
                            existing[key] = new_val
                
                # Merge lists (deduplicate)
                for key in ["成员", "功法", "宝物"]:
                    new_list = data.get(key, [])
                    if isinstance(new_list, list):
                        current_set = set(existing[key])
                        for item in new_list:
                            item_str = str(item)
                            if item_str not in current_set:
                                existing[key].append(item)
                                current_set.add(item_str)
    return final_data

def save_to_csv(data: Dict[str, Any], output_path: Path):
    """Save extracted data to CSV."""
    fieldnames = ["宗门名称", "行事风格", "总部", "成员", "功法", "宝物"]
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for sect_name, details in data.items():
            row = {
                "宗门名称": sect_name,
                "行事风格": details.get("行事风格", ""),
                "总部": details.get("总部", ""),
                "成员": ", ".join(map(str, details.get("成员", []))),
                "功法": ", ".join(map(str, details.get("功法", []))),
                "宝物": ", ".join(map(str, details.get("宝物", []))),
            }
            writer.writerow(row)
    print(f"Results saved to: {output_path}")

async def main():
    parser = argparse.ArgumentParser(description="Extract sect info from novel.")
    parser.add_argument("file", nargs="?", help="Path to the novel file")
    parser.add_argument("--test", action="store_true", help="Run in test mode (process first chunk only)")
    args = parser.parse_args()

    # Default path from previous file content, but check if exists
    default_path = Path(r"C:\Users\wangx\Desktop\幽冥仙途.txt")
    
    if args.file:
        novel_path = Path(args.file)
    elif default_path.exists():
        novel_path = default_path
    else:
        print(f"File not found: {default_path}")
        print("Usage: python extract.py <path_to_novel.txt> [--test]")
        return

    print(f"Reading novel from: {novel_path}")
    try:
        text = read_txt(novel_path)
    except Exception:
        print("UTF-8 read failed, trying GB18030...")
        try:
            with open(novel_path, "r", encoding="gb18030") as f:
                text = f.read()
        except Exception as e:
            print(f"Failed to read file: {e}")
            return

    chunks = split_text(text)
    print(f"Total text length: {len(text)}. Split into {len(chunks)} chunks.")

    if not chunks:
        print("No text to process.")
        return

    final_results = {}

    # Test mode logic
    if args.test:
        print("\n=== TEST MODE: Processing first 3 chunks only ===")
        chunks = chunks[:3]
    
    # Process chunks
    semaphore = asyncio.Semaphore(5) # Allow 5 concurrent requests
    
    async def sem_task(chunk, idx):
        async with semaphore:
            return await process_chunk(chunk, idx, len(chunks))

    tasks = [sem_task(chunk, i) for i, chunk in enumerate(chunks)]
    results = await asyncio.gather(*tasks)
    
    print("Merging results...")
    final_results = merge_results(results)
    print("Done!")

    # Save to CSV (common for both modes)
    save_to_csv(final_results, CSV_OUTPUT_PATH)

if __name__ == "__main__":
    asyncio.run(main())
