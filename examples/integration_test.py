#!/usr/bin/env python3
"""
Integration test example for SCIM client with real Cato Networks endpoint.

This script demonstrates how to use the SCIM client with real credentials
loaded from a .env file to make requests against a production Cato Networks
SCIM endpoint.

Prerequisites:
1. Create a .env file with your real Cato Networks SCIM credentials
2. Install dependencies: pip install -r requirements.txt

Usage:
    python examples/integration_test.py
"""

import sys
import os
import logging

# Add the parent directory to the path so we can import scimcp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scimcp import SCIMClient


def setup_logging():
    """Setup logging to see debug output."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_get_users():
    """Test retrieving users from SCIM endpoint."""
    print("=== Testing Get Users ===")
    
    try:
        client = SCIMClient()
        
        # Get first 10 users
        response = client.get_users(count=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results: {data.get('totalResults', 0)}")
            print(f"Items Per Page: {data.get('itemsPerPage', 0)}")
            print(f"Start Index: {data.get('startIndex', 0)}")
            
            resources = data.get('Resources', [])
            print(f"Retrieved {len(resources)} users")
            
            for i, user in enumerate(resources[:3]):  # Show first 3 users
                print(f"User {i+1}: {user.get('userName', 'N/A')} (ID: {user.get('id', 'N/A')})")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")


def test_get_groups():
    """Test retrieving groups from SCIM endpoint."""
    print("\n=== Testing Get Groups ===")
    
    try:
        client = SCIMClient()
        
        # Get first 10 groups
        response = client.get_groups(count=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total Results: {data.get('totalResults', 0)}")
            print(f"Items Per Page: {data.get('itemsPerPage', 0)}")
            print(f"Start Index: {data.get('startIndex', 0)}")
            
            resources = data.get('Resources', [])
            print(f"Retrieved {len(resources)} groups")
            
            for i, group in enumerate(resources[:3]):  # Show first 3 groups
                print(f"Group {i+1}: {group.get('displayName', 'N/A')} (ID: {group.get('id', 'N/A')})")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")


def test_user_filter():
    """Test filtering users by userName."""
    print("\n=== Testing User Filter ===")
    
    try:
        client = SCIMClient()
        
        # Example filter - adjust based on your actual users
        filter_expr = 'userName sw "test"'
        response = client.get_users(filter_expr=filter_expr)
        
        print(f"Status Code: {response.status_code}")
        print(f"Filter: {filter_expr}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Filtered Results: {data.get('totalResults', 0)}")
            
            resources = data.get('Resources', [])
            for user in resources:
                print(f"Filtered User: {user.get('userName', 'N/A')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run integration tests."""
    print("SCIM Client Integration Test")
    print("=" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("ERROR: .env file not found!")
        print("Please create a .env file with your SCIM credentials.")
        print("See .env.example for the required format.")
        return
    
    # Setup debug logging if DEBUG=true in .env
    if os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"):
        setup_logging()
        print("Debug logging enabled - you'll see detailed request/response info")
    
    # Run tests
    test_get_users()
    test_get_groups()
    test_user_filter()
    
    print("\n" + "=" * 40)
    print("Integration test completed!")


if __name__ == "__main__":
    main()