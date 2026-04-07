"""
Test script for tool_call_handler.py
"""

import json
from tools.tool_call_handler import extract_tool_calls, handle_tool_calling

def test_extract_tool_calls():
    """Test the extract_tool_calls function."""
    # Test case 1: Valid tool call
    text1 = '''
    Some text before
    {
      "tool_calls": [
        {
          "name": "store_memory",
          "parameters": {
            "name_of_issue": "P250217-03238",
            "summary": "BluetoothAgent not working",
            "entities_tags": ["defect", "issue", "S/W"],
            "importance": 0.8
          }
        }
      ]
    }
    Some text after
    '''
    
    result1 = extract_tool_calls(text1)
    print("Test 1 - Extract tool calls:")
    print(f"Input text: {text1}")
    print(f"Result: {result1}")
    assert result1 is not None
    assert len(result1) == 1
    assert result1[0]["name"] == "store_memory"
    assert result1[0]["parameters"]["name_of_issue"] == "P250217-03238"
    print("✓ Test 1 passed\n")
    
    # Test case 2: Multiple tool calls
    text2 = '''
    {
      "tool_calls": [
        {
          "name": "store_memory",
          "parameters": {
            "name_of_issue": "P250217-03238",
            "summary": "BluetoothAgent not working",
            "entities_tags": ["defect", "issue", "S/W"],
            "importance": 0.8
          }
        },
        {
          "name": "search_memory",
          "parameters": {
            "query": "BluetoothAgent"
          }
        }
      ]
    }
    '''
    
    result2 = extract_tool_calls(text2)
    print("Test 2 - Extract multiple tool calls:")
    print(f"Input text: {text2}")
    print(f"Result: {result2}")
    assert result2 is not None
    assert len(result2) == 2
    assert result2[0]["name"] == "store_memory"
    assert result2[1]["name"] == "search_memory"
    print("✓ Test 2 passed\n")
    
    # Test case 3: No tool calls
    text3 = "This is just regular text with no tool calls."
    
    result3 = extract_tool_calls(text3)
    print("Test 3 - No tool calls:")
    print(f"Input text: {text3}")
    print(f"Result: {result3}")
    assert result3 is None
    print("✓ Test 3 passed\n")

def test_handle_tool_calling():
    """Test the handle_tool_calling function."""
    # Test case 1: Valid tool call
    response_text1 = '''
    {
      "tool_calls": [
        {
          "name": "store_memory",
          "parameters": {
            "name_of_issue": "P250217-03238",
            "summary": "BluetoothAgent not working",
            "entities_tags": ["defect", "issue", "S/W"],
            "importance": 0.8
          }
        }
      ]
    }
    '''
    
    result1 = handle_tool_calling(response_text1)
    print("Test 1 - Handle tool calling:")
    print(f"Input response: {response_text1}")
    print(f"Result: {result1}")
    assert result1 is not None
    assert len(result1) == 1
    assert result1[0]["name"] == "store_memory"
    assert result1[0]["parameters"]["name_of_issue"] == "P250217-03238"
    print("✓ Test 1 passed\n")
    
    # Test case 2: No tool calls
    response_text2 = "This is just regular text with no tool calls."
    
    result2 = handle_tool_calling(response_text2)
    print("Test 2 - Handle no tool calls:")
    print(f"Input response: {response_text2}")
    print(f"Result: {result2}")
    assert result2 is None
    print("✓ Test 2 passed\n")

if __name__ == "__main__":
    print("Running tests for tool_call_handler.py...\n")
    test_extract_tool_calls()
    test_handle_tool_calling()
    print("All tests passed! ✓")