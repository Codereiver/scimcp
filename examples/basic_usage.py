#!/usr/bin/env python3
"""
Basic usage examples for the SCIM client.

This script shows common SCIM operations you can perform with the client.
"""

import sys
import os

# Add the parent directory to the path so we can import scimcp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scimcp import SCIMClient


def example_create_user():
    """Example of creating a new user with automatic generation of externalId and password."""
    client = SCIMClient()
    
    response = client.create_user(
        email="newuser@example.com",
        firstName="New",
        lastName="User"
    )
    
    if response.status_code == 201:
        created_user = response.json()
        print(f"Created user: {created_user['id']}")
        print(f"Generated external ID: {created_user.get('externalId', 'N/A')}")
        return created_user['id']
    else:
        print(f"Failed to create user: {response.status_code} - {response.text}")
        return None


def example_create_user_with_custom_values():
    """Example of creating a new user with custom externalId and password."""
    client = SCIMClient()
    
    response = client.create_user(
        email="customuser@example.com",
        firstName="Custom",
        lastName="User",
        externalId="CUSTOM123",
        password="MySecurePassword123!"
    )
    
    if response.status_code == 201:
        created_user = response.json()
        print(f"Created user with custom values: {created_user['id']}")
        return created_user['id']
    else:
        print(f"Failed to create user: {response.status_code} - {response.text}")
        return None


def example_get_user(user_id):
    """Example of retrieving a user by ID."""
    client = SCIMClient()
    
    response = client.get_user(user_id)
    
    if response.status_code == 200:
        user = response.json()
        print(f"Retrieved user: {user['userName']}")
        return user
    else:
        print(f"Failed to get user: {response.status_code} - {response.text}")
        return None


def example_update_user(user_id):
    """Example of updating a user."""
    client = SCIMClient()
    
    # First get the current user data
    response = client.get_user(user_id)
    if response.status_code != 200:
        print("Failed to get user for update")
        return False
    
    user_data = response.json()
    
    # Update the user's given name
    user_data['name']['givenName'] = "Updated"
    
    response = client.update_user(user_id, user_data)
    
    if response.status_code == 200:
        updated_user = response.json()
        print(f"Updated user: {updated_user['name']['givenName']}")
        return True
    else:
        print(f"Failed to update user: {response.status_code} - {response.text}")
        return False


def example_list_users_with_pagination():
    """Example of listing users with pagination."""
    client = SCIMClient()
    
    page_size = 10
    start_index = 1
    
    while True:
        response = client.get_users(start_index=start_index, count=page_size)
        
        if response.status_code != 200:
            print(f"Failed to get users: {response.status_code} - {response.text}")
            break
        
        data = response.json()
        users = data.get('Resources', [])
        
        if not users:
            print("No more users found")
            break
        
        print(f"Page {(start_index - 1) // page_size + 1}:")
        for user in users:
            print(f"  - {user['userName']} (ID: {user['id']})")
        
        # Check if there are more results
        if len(users) < page_size or start_index + len(users) >= data.get('totalResults', 0):
            break
        
        start_index += page_size


def example_search_users():
    """Example of searching users with filters."""
    client = SCIMClient()
    
    # Search for users whose userName starts with "test"
    filter_expr = 'userName sw "test"'
    
    response = client.get_users(filter_expr=filter_expr)
    
    if response.status_code == 200:
        data = response.json()
        users = data.get('Resources', [])
        
        print(f"Found {len(users)} users matching filter '{filter_expr}':")
        for user in users:
            print(f"  - {user['userName']}")
    else:
        print(f"Search failed: {response.status_code} - {response.text}")


def example_create_group():
    """Example of creating a new group with automatic generation of externalId."""
    client = SCIMClient()
    
    response = client.create_group(displayName="Test Group")
    
    if response.status_code == 201:
        created_group = response.json()
        print(f"Created group: {created_group['id']}")
        print(f"Generated external ID: {created_group.get('externalId', 'N/A')}")
        return created_group['id']
    else:
        print(f"Failed to create group: {response.status_code} - {response.text}")
        return None


def example_create_group_with_custom_external_id():
    """Example of creating a new group with custom externalId."""
    client = SCIMClient()
    
    response = client.create_group(
        displayName="Custom Group",
        externalId="GRP12345"
    )
    
    if response.status_code == 201:
        created_group = response.json()
        print(f"Created group with custom external ID: {created_group['id']}")
        return created_group['id']
    else:
        print(f"Failed to create group: {response.status_code} - {response.text}")
        return None


def main():
    """Run basic usage examples."""
    print("SCIM Client Basic Usage Examples")
    print("=" * 40)
    
    # Check if credentials are available
    if not os.getenv("SCIM_BASE_URL") or not os.getenv("SCIM_TOKEN"):
        print("ERROR: SCIM credentials not found!")
        print("Please set SCIM_BASE_URL and SCIM_TOKEN environment variables")
        print("or create a .env file with these values.")
        return
    
    print("\n1. Listing users with pagination:")
    example_list_users_with_pagination()
    
    print("\n2. Searching users:")
    example_search_users()
    
    print("\n3. Creating a group:")
    group_id = example_create_group()
    
    # Uncomment these if you want to test user creation/modification
    # WARNING: These will create/modify real data!
    
    # print("\n4. Creating a user with auto-generated values:")
    # user_id = example_create_user()
    
    # print("\n5. Creating a user with custom values:")
    # user_id2 = example_create_user_with_custom_values()
    
    # if user_id:
    #     print("\n6. Getting the created user:")
    #     example_get_user(user_id)
    #     
    #     print("\n7. Updating the user:")
    #     example_update_user(user_id)
    
    print("\n" + "=" * 40)
    print("Examples completed!")


if __name__ == "__main__":
    main()