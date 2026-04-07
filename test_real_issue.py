"""
Test script for processing a real issue with the Gauss model.
"""

import asyncio
import json
from models.gauss_model import GaussModel
from google.adk.models.llm_request import LlmRequest
from google.genai import types

async def test_real_issue():
    """Test processing a real issue with the Gauss model."""
    print("Testing Gauss model with a real issue...")
    
    # Initialize the Gauss model
    try:
        model = GaussModel()
        print(f"✓ GaussModel initialized with model_id: {model._model_id}")
    except Exception as e:
        print(f"✗ Failed to initialize GaussModel: {e}")
        return
    
    # Load the test issue
    try:
        with open('test_issue.json', 'r', encoding='utf-8') as f:
            issue_data = json.load(f)
        print("✓ Test issue loaded successfully")
        print(f"Issue data: {json.dumps(issue_data, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"✗ Failed to load test issue: {e}")
        return
    
    # Create a test request with the real issue data
    try:
        # Create content parts with the real issue
        content_text = f'''
Please process this issue information and store it in memory:

Issue: {issue_data["defectCode"]}
Title: {issue_data["title"]}
Summary: {issue_data["contentSummary"]}
Category: {issue_data["category"]}
Cause: {issue_data["cause"]}
Countermeasure: {issue_data["countermeasure"]}
'''
        
        parts = [types.Part.from_text(text=content_text)]
        contents = [types.Content(role="user", parts=parts)]
        
        # Create system instruction with tool calling format
        system_instruction = '''
You are a helpful assistant that processes issue information. When you need to use tools, you MUST respond with a JSON object containing a "tool_calls" array. This is the ONLY accepted format.

Required Format:
{
  "tool_calls": [
    {
      "name": "tool_name",
      "parameters": {
        "param1": "value1",
        "param2": "value2"
      }
    }
  ]
}

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
{
  "tool_calls": [
    {
      "name": "store_memory",
      "parameters": {
        "name_of_issue": "P250217-03238",
        "summary": "BluetoothAgent not working due to missing ISehBluetooth",
        "entities_tags": ["defect", "issue", "S/W"],
        "importance": 0.8
      }
    }
  ]
}

- To search memory:
{
  "tool_calls": [
    {
      "name": "search_memory",
      "parameters": {
        "query": "BluetoothAgent not responding"
      }
    }
  ]
}

CRITICAL: 
- ONLY this JSON format is accepted
- Any other format will be automatically rejected
- DO NOT explain your tool calling plan verbally
- Your entire response must be ONLY the JSON object
- You MUST use the tool calling format for the given issue information
'''
        
        # Create LLM request
        request = LlmRequest(
            contents=contents
        )
        
        print("\n" + "="*50)
        print("REQUEST TO GAUSS MODEL")
        print("="*50)
        print(f"Content:\n{content_text}")
        print(f"System Instruction:\n{system_instruction}")
        print("="*50)
        
    except Exception as e:
        print(f"✗ Failed to create LLM request with real issue: {e}")
        return
    
    # Test generate_content_async with the real issue
    try:
        print("\nSending request to Gauss model...")
        response_count = 0
        
        async for response in model.generate_content_async(request, system_instruction=system_instruction):
            response_count += 1
            print(f"\nResponse {response_count}:")
            print("="*50)
            print("RESPONSE FROM GAUSS MODEL")
            print("="*50)
            print(f"  Model version: {response.model_version}")
            print(f"  Finish reason: {response.finish_reason}")
            
            if response.error_message:
                print(f"  Error: {response.error_message}")
            elif response.content:
                # Print content parts
                if response.content.parts:
                    for i, part in enumerate(response.content.parts):
                        if hasattr(part, 'text') and part.text:
                            print(f"  Part {i+1} (text): {part.text}")
                        elif hasattr(part, 'function_call') and part.function_call:
                            print(f"  Part {i+1} (function_call): {part.function_call}")
                        else:
                            print(f"  Part {i+1}: {type(part)}")
                else:
                    print(f"  Content: {response.content}")
            else:
                print("  No content in response")
            print("="*50)
        
        print(f"\n✓ Successfully received {response_count} responses from Gauss model")
        
    except Exception as e:
        print(f"✗ Failed to generate content with Gauss model for real issue: {e}")
        return
    
    print("\nReal issue test completed successfully! ✓")

async def main():
    """Main test function."""
    print("Running real issue test with Gauss model...\n")
    await test_real_issue()
    print("\nAll tests completed! ✓")

if __name__ == "__main__":
    asyncio.run(main())