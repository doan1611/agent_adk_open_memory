"""
Memory tools for the issue tracking system.
"""

import json

from openmemory import Memory
from pathlib import Path
from datetime import datetime

# Initialize OpenMemory
memory = Memory()

async def store_memory(name_of_issue: str, summary: str, entities_tags: list, importance: float) -> str:
    """
    Store memory with openmemory. Reads the JSON file in the case_path directory
    that matches the given issue name, stores it with additional metadata, and deletes the file.
    """
    print("\n👋 add memory!")
    case_path = Path("./inbox")
    processed_file = Path("./processed.json")
    
    if not case_path.is_dir():
        return f"case_path {case_path} is not a directory."
    
    # Ensure the filename ends with a single .json extension
    target_file = case_path / Path(name_of_issue).with_suffix('.json')
    if not target_file.is_file():
        return f"No file found for issue '{name_of_issue}'."
    
    try:
        raw = json.loads(target_file.read_text(encoding="utf-8"))
        # Add additional metadata
        raw["summary"] = summary
        raw["entities_tags"] = entities_tags
        raw["importance"] = importance
        
        await memory.add(
            content=json.dumps(raw, ensure_ascii=False, indent=2),
            tags=["plm_case"],
        )
        
        # Ghi thông tin vào file processed.json
        processed_data = []
        if processed_file.is_file():
            try:
                processed_data = json.loads(processed_file.read_text(encoding="utf-8"))
            except:
                pass
        
        # Thêm thông tin file đã xử lý
        processed_entry = {
            "filename": target_file.name,
            "processed_at": datetime.now().isoformat(),
            "defect_code": raw.get("defectCode", name_of_issue)
        }
        processed_data.append(processed_entry)
        
        # Lưu lại file processed.json
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        target_file.unlink()
        return f"Memory stored for issue '{name_of_issue}'."
    except Exception as e:
        return f"Error processing issue '{name_of_issue}': {str(e)}"

async def search_memory(query: str) -> str:
    """
    Semantic search
    """
    print("search_memory")
    results = await memory.search(
        query,
        tags=["plm_case"],
        limit=5,
    )

    
    if not results:
        return "No memory found."

    # Handle different result formats
    texts = []
    for r in results:
        if "text" in r:
            texts.append(r["text"])
        elif "content" in r:
            texts.append(r["content"])
        else:
            texts.append(str(r))
    
    return "\n".join(texts)
