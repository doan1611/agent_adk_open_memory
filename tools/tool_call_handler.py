"""
Tool call handler for processing tool calls from Gauss model.
"""

import json

from tools.parser import extract_tool_calls

def handle_tool_calling(response_text):
    """
    Handle tool calling by parsing JSON response and converting to function calls
    """
    print(f"Handling tool calling for response: {response_text}")
    
    # Try to extract function calls from the model response
    tool_calls_list = extract_tool_calls(response_text)
    
    if tool_calls_list and isinstance(tool_calls_list, list):
        # Process each tool call
        results = []
        for tool_call in tool_calls_list:
            if isinstance(tool_call, dict) and 'name' in tool_call and 'parameters' in tool_call:
                func_name = tool_call['name']
                parameters = tool_call['parameters']
                
                # Add to results
                results.append({
                    "name": func_name,
                    "parameters": parameters
                })
        
        print(f"Tool calling results: {results}")
        return results if results else None
    
    print("No tool calls found in response")
    return None
