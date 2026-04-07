"""
Test script to verify search_memory tool is working correctly.
"""

import asyncio
import json
from tools.memory_tools import search_memory

async def test_search_tool():
    """Test the search_memory tool directly."""
    print("Testing search_memory tool...")
    
    # Test searching for "BluetoothAgent"
    query = "doan dep trai"
    print(f"Searching for: {query}")
    
    result = await search_memory(query)
    print(f"Search result:\n{result}")

if __name__ == "__main__":
    asyncio.run(test_search_tool())