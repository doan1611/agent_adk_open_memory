"""
Test script for Gauss model integration.
"""

import asyncio
import json
import os
from models.gauss_model import GaussModel
from google.adk.models.llm_request import LlmRequest
from google.genai import types

async def test_gauss_model():
    """Test the Gauss model integration."""
    print("Testing Gauss model integration...")
    
    # Initialize the Gauss model
    try:
        model = GaussModel()
        print(f"✓ GaussModel initialized with model_id: {model._model_id}")
    except Exception as e:
        print(f"✗ Failed to initialize GaussModel: {e}")
        return
    
    # Create a simple test request
    try:
        # Create content parts
        parts = [types.Part.from_text(text="Hello, this is a test message. Please respond with a short greeting.")]
        
        # Create contents
        contents = [types.Content(role="user", parts=parts)]
        
        # Create LLM request
        request = LlmRequest(
            contents=contents
        )
        
        print("✓ LLM request created successfully")
        print(f"Request content: {request.contents[0].parts[0].text}")
        
    except Exception as e:
        print(f"✗ Failed to create LLM request: {e}")
        return
    
    # Test generate_content_async
    try:
        print("\nSending request to Gauss model...")
        response_count = 0
        
        async for response in model.generate_content_async(request):
            response_count += 1
            print(f"Response {response_count}:")
            print(f"  Model version: {response.model_version}")
            print(f"  Finish reason: {response.finish_reason}")
            
            if response.error_message:
                print(f"  Error: {response.error_message}")
            elif response.content:
                # Print content parts
                if response.content.parts:
                    for i, part in enumerate(response.content.parts):
                        if hasattr(part, 'text') and part.text:
                            print(f"  Part {i+1} (text): {part.text[:200]}...")
                        elif hasattr(part, 'function_call') and part.function_call:
                            print(f"  Part {i+1} (function_call): {part.function_call}")
                        else:
                            print(f"  Part {i+1}: {type(part)}")
                else:
                    print(f"  Content: {response.content}")
            else:
                print("  No content in response")
        
        print(f"✓ Successfully received {response_count} responses from Gauss model")
        
    except Exception as e:
        print(f"✗ Failed to generate content with Gauss model: {e}")
        return
    
    print("\nGauss model test completed successfully! ✓")

async def test_gauss_with_tool_call():
    """Test the Gauss model with tool calling format."""
    print("\nTesting Gauss model with tool calling format...")
    
    # Initialize the Gauss model
    try:
        model = GaussModel()
        print(f"✓ GaussModel initialized with model_id: {model._model_id}")
    except Exception as e:
        print(f"✗ Failed to initialize GaussModel: {e}")
        return
    
    # Create a test request with tool calling instructions
    try:
        # Create content parts with a test issue
        content_text = '''
Please process this issue information and store it in memory:

Issue: P250217-03238
Title: [REP][YB1] [A346N] BluetoothAgent(com.sec.android.app.bluetoothagent,35.15) / Application not responding[ACT][3rdAppAuto]
Summary: Not merge ISehBluetooth\r\n=> Can not use ISehBluetooth HIDL or AIDL, BluetoothAgent not work
Category: S/W
Cause: Not merge ISehBluetooth\r\n=> Can not use ISehBluetooth HIDL or AIDL, BluetoothAgent not work
Countermeasure: Merge ISehBluetooth AIDL
'''
        
        parts = [types.Part.from_text(text=content_text)]
        
        # Create contents
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
        
        print("✓ LLM request with tool calling instructions created successfully")
        print(f"Request content: {request.contents[0].parts[0].text[:100]}...")
        
    except Exception as e:
        print(f"✗ Failed to create LLM request with tool calling instructions: {e}")
        return
    
    # Test generate_content_async with tool calling
    try:
        print("\nSending tool calling request to Gauss model...")
        response_count = 0
        
        async for response in model.generate_content_async(request, system_instruction=system_instruction):
            response_count += 1
            print(f"Response {response_count}:")
            print(f"  Model version: {response.model_version}")
            print(f"  Finish reason: {response.finish_reason}")
            
            if response.error_message:
                print(f"  Error: {response.error_message}")
            elif response.content:
                # Print content parts
                if response.content.parts:
                    for i, part in enumerate(response.content.parts):
                        if hasattr(part, 'text') and part.text:
                            print(f"  Part {i+1} (text): {part.text[:300]}...")
                        elif hasattr(part, 'function_call') and part.function_call:
                            print(f"  Part {i+1} (function_call): {part.function_call}")
                        else:
                            print(f"  Part {i+1}: {type(part)}")
                else:
                    print(f"  Content: {response.content}")
            else:
                print("  No content in response")
        
        print(f"✓ Successfully received {response_count} responses from Gauss model with tool calling")
        
    except Exception as e:
        print(f"✗ Failed to generate content with Gauss model for tool calling: {e}")
        return
    
    print("\nGauss model tool calling test completed successfully! ✓")

async def main():
    """Main test function."""
    print("Running Gauss model tests...\n")
    
    # Run basic Gauss model test
    await test_gauss_model()
    
    # Run Gauss model with tool calling test
    await test_gauss_with_tool_call()
    
    print("\nAll Gauss model tests completed! ✓")

if __name__ == "__main__":
    asyncio.run(main())