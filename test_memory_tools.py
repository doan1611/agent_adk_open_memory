"""
Test script for memory_tools.py
"""

import asyncio
import json
import os
from tools.memory_tools import store_memory, search_memory

def create_test_issue_file():
    """Create a test issue file in the inbox directory."""
    # Create inbox directory if it doesn't exist
    os.makedirs("inbox", exist_ok=True)
    
    # Create test issue file
    test_issue = {
        "defectCode": "TEST-001",
        "title": "Test Issue for Memory Tools",
        "contentSummary": "This is a test issue to verify memory tools functionality",
        "category": "Test",
        "cause": "Testing purposes",
        "countermeasure": "Run tests"
    }
    
    with open("inbox/TEST-001.json", "w", encoding="utf-8") as f:
        json.dump(test_issue, f, indent=2, ensure_ascii=False)
    
    print("Created test issue file: inbox/TEST-001.json")

async def test_store_memory():
    """Test the store_memory function."""
    print("Testing store_memory function...")
    
    # Create test issue file first
    create_test_issue_file()
    
    # Test storing memory
    result = await store_memory(
        name_of_issue="TEST-001",
        summary="Test issue for memory tools",
        entities_tags=["test", "issue"],
        importance=0.5
    )
    
    print(f"Store memory result: {result}")
    assert "Memory stored for issue 'TEST-001'" in result
    print("✓ store_memory test passed\n")
    
    # Check that file was deleted
    assert not os.path.exists("inbox/TEST-001.json")
    print("✓ Issue file was correctly deleted after storing\n")

async def test_search_memory():
    """Test the search_memory function."""
    print("Testing search_memory function...")
    
    # Search for the stored memory
    result = await search_memory("test issue")
    
    print(f"Search memory result: {result}")
    # Note: The result may vary depending on OpenMemory's search implementation
    # but it should not be an error
    assert "Error" not in result
    print("✓ search_memory test passed\n")

async def run_tests():
    """Run all tests."""
    print("Running tests for memory_tools.py...\n")
    
    try:
        await test_store_memory()
        await test_search_memory()
        print("All tests passed! ✓")
    except Exception as e:
        print(f"Test failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_tests())