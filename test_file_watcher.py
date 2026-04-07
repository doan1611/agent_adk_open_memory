"""
Test script for file_watcher.py
"""

import asyncio
import json
import os
import time
from pathlib import Path
from agents.ingest_agent import create_ingest_agent
from models.gauss_model import GaussModel
from watcher.file_watcher import watch_folder

def create_test_issue_file():
    """Create a test issue file in the inbox directory."""
    # Create inbox directory if it doesn't exist
    os.makedirs("inbox", exist_ok=True)
    
    # Create test issue file
    test_issue = {
        "defectCode": "TEST-003",
        "title": "Test Issue for File Watcher",
        "contentSummary": "This is a test issue to verify file watcher functionality",
        "category": "Test",
        "cause": "Testing purposes",
        "countermeasure": "Run tests"
    }
    
    with open("inbox/TEST-003.json", "w", encoding="utf-8") as f:
        json.dump(test_issue, f, indent=2, ensure_ascii=False)
    
    print("Created test issue file: inbox/TEST-003.json")

async def test_watch_folder():
    """Test the watch_folder function."""
    print("Testing watch_folder function...")
    
    # Create test issue file
    create_test_issue_file()
    
    model = GaussModel()
    ingest_agent = create_ingest_agent(model)
    inbox_path = Path("./inbox")

    start_time = time.time()

    try:
        await asyncio.wait_for(
            watch_folder(ingest_agent, inbox_path, poll_interval=1),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        # This is expected as the watcher runs indefinitely
        pass
    
    elapsed_time = time.time() - start_time
    print(f"Watcher ran for {elapsed_time:.2f} seconds")
    
    # Check if the file was processed (should be deleted)
    file_exists = os.path.exists("inbox/TEST-003.json")
    print(f"File exists after watching: {file_exists}")
    
    # Note: We can't easily verify the processing result without mocking
    # the agent, but we can check that the function runs without errors
    print("✓ watch_folder test completed (no errors)\n")

async def run_tests():
    """Run all file watcher tests."""
    print("Running tests for file_watcher.py...\n")
    
    try:
        await test_watch_folder()
        print("File watcher tests completed! ✓")
    except Exception as e:
        print(f"File watcher tests failed with error: {e}")
        raise

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests())