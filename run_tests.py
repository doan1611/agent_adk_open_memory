"""
Main test runner for the issue tracking system.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def run_all_tests():
    """Run all test scripts."""
    print("Running all tests for the issue tracking system...\n")
    
    # Import test modules
    from test_tool_call_handler import test_extract_tool_calls, test_handle_tool_calling
    from test_memory_tools import run_tests as test_memory_tools
    from test_file_watcher import run_tests as test_file_watcher
    from test_http_server import run_tests as test_http_server
    
    try:
        # Run tool_call_handler tests
        print("=" * 50)
        print("Testing tool_call_handler.py")
        print("=" * 50)
        test_extract_tool_calls()
        test_handle_tool_calling()
        print("✓ tool_call_handler tests passed\n")
        
        # Run memory_tools tests
        print("=" * 50)
        print("Testing memory_tools.py")
        print("=" * 50)
        await test_memory_tools()
        print("✓ memory_tools tests passed\n")
        
        # Run file_watcher tests
        print("=" * 50)
        print("Testing file_watcher.py")
        print("=" * 50)
        await test_file_watcher()
        print("✓ file_watcher tests passed\n")
        
        # Note: HTTP server tests require the server to be running
        # These should be run manually after starting the server
        print("=" * 50)
        print("HTTP server tests")
        print("=" * 50)
        print("To test HTTP server endpoints:")
        print("1. Start the server: python main.py")
        print("2. In another terminal: python test_http_server.py")
        print("✓ HTTP server tests skipped (run manually)\n")
        
        print("=" * 50)
        print("All tests completed successfully! ✓")
        print("=" * 50)
        
    except Exception as e:
        print(f"Tests failed with error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_all_tests())