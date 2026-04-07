"""
Test script for HTTP server endpoints.
"""

import asyncio
import aiohttp
import json
import time
from aiohttp import web

# Test data
test_issue_data = {
    "defectCode": "TEST-002",
    "title": "Test Issue for HTTP Server",
    "contentSummary": "This is a test issue to verify HTTP server functionality",
    "category": "Test",
    "cause": "Testing purposes",
    "countermeasure": "Run tests"
}

async def test_ingest_endpoint():
    """Test the /ingest endpoint."""
    print("Testing /ingest endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8081/ingest",
                json=test_issue_data
            ) as response:
                status = response.status
                data = await response.json()
                print(f"Ingest response status: {status}")
                print(f"Ingest response data: {data}")
                
                # Check if the request was successful
                assert status == 200
                assert "status" in data
                assert data["status"] == "ingested"
                print("✓ /ingest endpoint test passed\n")
                
    except aiohttp.ClientConnectorError:
        print("✗ Failed to connect to server. Make sure the server is running on http://localhost:8081")
        raise
    except Exception as e:
        print(f"✗ /ingest endpoint test failed with error: {e}")
        raise

async def test_search_endpoint():
    """Test the /search endpoint."""
    print("Testing /search endpoint...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8081/search?q=test+issue"
            ) as response:
                status = response.status
                data = await response.json()
                print(f"Search response status: {status}")
                print(f"Search response data: {data}")
                
                # Check if the request was successful
                assert status == 200
                assert "query" in data
                assert "response" in data
                print("✓ /search endpoint test passed\n")
                
    except aiohttp.ClientConnectorError:
        print("✗ Failed to connect to server. Make sure the server is running on http://localhost:8081")
        raise
    except Exception as e:
        print(f"✗ /search endpoint test failed with error: {e}")
        raise

async def run_tests():
    """Run all HTTP server tests."""
    print("Running tests for HTTP server endpoints...\n")
    
    # Wait a moment for server to start if it was just launched
    time.sleep(1)
    
    try:
        await test_ingest_endpoint()
        await test_search_endpoint()
        print("All HTTP server tests passed! ✓")
    except Exception as e:
        print(f"HTTP server tests failed with error: {e}")
        raise

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests())