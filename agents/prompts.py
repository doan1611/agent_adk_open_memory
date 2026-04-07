"""
Prompts for the agent system.
"""

FUNCTION_CALLING_INSTRUCTIONS = """
<tool_calling_format>
When you need to use tools, you MUST respond with a JSON object containing a "tool_calls" array. This is the ONLY accepted format.

Required Format:
{{
  "tool_calls": [
    {{
      "name": "tool_name",
      "parameters": {{
        "param1": "value1",
        "param2": "value2"
      }}
    }}
  ]
}}

Available tools:
1. **`store_memory`**: Lưu thông tin issue vào OpenMemory
   - `name_of_issue`: Tên của issue (defectCode)
   - `summary`: Tóm tắt nội dung issue
   - `entities_tags`: Các tag liên quan đến issue
   - `importance`: Mức độ quan trọng (0.0 - 1.0)

2. **`search_memory`**: Tìm kiếm thông tin trong OpenMemory
   - `query`: Từ khóa tìm kiếm

Examples:
- To store an issue:
{{
  "tool_calls": [
    {{
      "name": "store_memory",
      "parameters": {{
        "name_of_issue": "P250217-03238",
        "summary": "BluetoothAgent not working due to missing ISehBluetooth",
        "entities_tags": ["defect", "issue", "S/W"],
        "importance": 0.8
      }}
    }}
  ]
}}

- To search memory:
{{
  "tool_calls": [
    {{
      "name": "search_memory",
      "parameters": {{
        "query": "BluetoothAgent not responding"
      }}
    }}
  ]
}}

CRITICAL: 
- ONLY this JSON format is accepted
- Any other format will be automatically rejected
- DO NOT explain your tool calling plan verbally
- Your entire response must be ONLY the JSON object
</tool_calling_format>
"""