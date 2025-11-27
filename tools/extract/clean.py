import asyncio
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.utils.llm import call_llm_json

INPUT_CSV_PATH = project_root / "tools" / "extract" / "res.csv"
OUTPUT_CSV_PATH = project_root / "tools" / "extract" / "cleaned_res.csv"
CONCURRENCY_LIMIT = 5

CLEAN_PROMPT_TEMPLATE = """
你是一位修仙小说数据整理专家。
请清理以下宗门信息，去除冗余和重复的内容。

原始信息：
{sect_info}

要求：
1. **去重**：成员、功法、宝物列表中的重复项请去除。
2. **精简**：行事风格和总部的描述如果重复或啰嗦，请合并精简，保留核心信息。
3. **格式**：返回标准的 JSON 格式，结构如下。
4. **保留**: 有意义的信息要保留住

返回格式：
{
  "宗门名称": {
    "行事风格": "精简后的描述",
    "总部": "精简后的描述",
    "成员": ["成员1", "成员2"],
    "功法": ["功法1", "功法2"],
    "宝物": ["宝物1"]
  }
}

注意：
- 如果原始信息中某些字段为空，保持为空。
- 不要编造未提供的信息。
- "宗门名称"必须与输入一致。
"""

async def process_row(row: Dict[str, str], semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    """Process a single CSV row using LLM."""
    async with semaphore:
        # Convert row to a cleaner string representation or just pass the dict
        # We pass the dict as a JSON string to preserve structure for the LLM
        sect_info_str = json.dumps(row, ensure_ascii=False, indent=2)
        
        prompt = CLEAN_PROMPT_TEMPLATE.replace("{sect_info}", sect_info_str)
        
        try:
            print(f"Processing: {row.get('宗门名称', 'Unknown')}")
            result = await call_llm_json(prompt)
            return result
        except Exception as e:
            print(f"Error processing {row.get('宗门名称', 'Unknown')}: {e}")
            return {}

def merge_cleaned_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge the cleaned results."""
    final_data = {}
    
    for result in results:
        if not result:
            continue
            
        # Check if it's a flat structure (e.g. { "宗门名称": "SectName", "行事风格": ... })
        if "宗门名称" in result and isinstance(result["宗门名称"], str):
            sect_name = result["宗门名称"]
            # Treat the whole result as data, minus the name
            data = {k: v for k, v in result.items() if k != "宗门名称"}
            # Normalize to the expected iteration structure
            items_to_process = {sect_name: data}
        else:
            items_to_process = result

        for sect_name, data in items_to_process.items():
            if not isinstance(data, dict):
                # This might happen if items_to_process came from a weirdly structured result
                # or if we failed to detect flat structure correctly (e.g. "宗门名称" missing)
                print(f"Warning: Unexpected data format for sect {sect_name}, skipping. Data type: {type(data)}, Value: {data}")
                continue
                
            if sect_name not in final_data:
                final_data[sect_name] = {
                    "行事风格": data.get("行事风格", ""),
                    "总部": data.get("总部", ""),
                    "成员": data.get("成员", []) if isinstance(data.get("成员"), list) else [],
                    "功法": data.get("功法", []) if isinstance(data.get("功法"), list) else [],
                    "宝物": data.get("宝物", []) if isinstance(data.get("宝物"), list) else [],
                }
            else:
                # If we encounter the same sect again (shouldn't happen if input is unique, but good for safety)
                existing = final_data[sect_name]
                
                # Merge text fields
                for key in ["行事风格", "总部"]:
                    new_val = data.get(key, "")
                    if new_val and new_val not in existing[key]:
                        existing[key] = existing[key] + " | " + new_val if existing[key] else new_val
                
                # Merge lists
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
    if not INPUT_CSV_PATH.exists():
        print(f"Input file not found: {INPUT_CSV_PATH}")
        return

    print(f"Reading from {INPUT_CSV_PATH}")
    rows = []
    with open(INPUT_CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No data found in CSV.")
        return

    print(f"Found {len(rows)} rows. Starting processing...")
    
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    tasks = [process_row(row, semaphore) for row in rows]
    
    results = await asyncio.gather(*tasks)
    
    print("Merging and saving results...")
    final_data = merge_cleaned_results(results)
    save_to_csv(final_data, OUTPUT_CSV_PATH)
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())

