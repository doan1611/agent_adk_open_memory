"""
Simple test script for processing a real issue with the Gauss model.
"""

import asyncio
import json
from models.gauss_model import GaussModel
from google.adk.models.llm_request import LlmRequest
from google.genai import types
from agents.prompts import FUNCTION_CALLING_INSTRUCTIONS

async def test_simple():
    """Simple test with request and response only."""
    # Initialize the Gauss model
    model = GaussModel()
    
    # Load the test issue
    with open('test_issue.json', 'r', encoding='utf-8') as f:
        issue_data = json.load(f)
    
    # Create content with the real issue
    content_text = f'''
Issue: {issue_data["defectCode"]}
Title: {issue_data["title"]}
Summary: {issue_data["contentSummary"]}
Category: {issue_data["category"]}
Cause: {issue_data["cause"]}
Countermeasure: {issue_data["countermeasure"]}
'''
    
    parts = [types.Part.from_text(text=content_text)]
    contents = [types.Content(role="user", parts=parts)]
    
    # Create system instruction using the shared prompt
    system_instruction = f'''
You are a helpful assistant that processes issue information. When you need to use tools, you MUST respond with a JSON object containing a "tool_calls" array.
{FUNCTION_CALLING_INSTRUCTIONS}
'''
    
    # Create LLM request
    request = LlmRequest(
        contents=contents
    )
    
    # Print request
    print("REQUEST:")
    print("=" * 40)
    print(content_text.strip())
    print("\nSystem Instruction:")
    print(system_instruction.strip())
    print("=" * 40)
    
    # Send request to Gauss model
    async for response in model.generate_content_async(request, system_instruction=system_instruction):
        if response.content and response.content.parts:
            print("\nRESPONSE:")
            print("=" * 40)
            for part in response.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(part.text)
                elif hasattr(part, 'function_call') and part.function_call:
                    print(f"Function Call: {part.function_call.name}")
                    print(f"Parameters: {part.function_call.args}")
            print("=" * 40)

async def main():
    """Main function."""
    await test_simple()

if __name__ == "__main__":
    asyncio.run(main())
