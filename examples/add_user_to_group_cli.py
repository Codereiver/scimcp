#!/usr/bin/env python3
"""
CLI tool for adding a user to a group via SCIM API.

This script allows you to add a user to a group by providing the group name
and user email. It will automatically look up the user and group IDs, then
update the group membership.

Usage:
    python examples/add_user_to_group_cli.py --group "Administrators" --email user@example.com
    python examples/add_user_to_group_cli.py --group "Sales Team" --email john.doe@company.com --debug
"""

import sys
import os
import argparse
import logging
import json

# Add the parent directory to the path so we can import scimcp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scimcp import SCIMClient


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def find_user_by_email(client: SCIMClient, email: str):
    """Find user by email address."""
    print(f"🔍 Looking for user with email: {email}")
    
    # Use SCIM filter to find user by email
    filter_expr = f'emails.value eq "{email}"'
    response = client.get_users(filter_expr=filter_expr)
    
    if response.status_code != 200:
        print(f"❌ Failed to search for user: {response.status_code}")
        return None
    
    data = response.json()
    users = data.get('Resources', [])
    
    if not users:
        print(f"❌ No user found with email: {email}")
        return None
    
    if len(users) > 1:
        print(f"⚠️  Multiple users found with email {email}, using first match")
    
    user = users[0]
    print(f"✅ Found user: {user.get('userName')} (ID: {user.get('id')})")
    return user


def find_group_by_name(client: SCIMClient, group_name: str):
    """Find group by display name."""
    print(f"🔍 Looking for group with name: {group_name}")
    
    # Use SCIM filter to find group by display name
    filter_expr = f'displayName eq "{group_name}"'
    response = client.get_groups(filter_expr=filter_expr)
    
    if response.status_code != 200:
        print(f"❌ Failed to search for group: {response.status_code}")
        return None
    
    data = response.json()
    groups = data.get('Resources', [])
    
    if not groups:
        print(f"❌ No group found with name: {group_name}")
        return None
    
    if len(groups) > 1:
        print(f"⚠️  Multiple groups found with name '{group_name}', using first match")
    
    group = groups[0]
    current_members = group.get('members', [])
    print(f"✅ Found group: {group.get('displayName')} (ID: {group.get('id')}, Members: {len(current_members)})")
    return group


def is_user_in_group(group: dict, user_id: str) -> bool:
    """Check if user is already a member of the group."""
    members = group.get('members', [])
    return any(member.get('value') == user_id for member in members)


def add_user_to_group_cli():
    """Add user to group via command line interface."""
    parser = argparse.ArgumentParser(
        description='Add a user to a group via Cato Networks SCIM API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --group "Administrators" --email admin@company.com
  %(prog)s --group "Sales Team" --email john.doe@company.com
  %(prog)s --group "IT Department" --email tech@company.com --debug
  %(prog)s --group "Marketing" --email mary@company.com --dry-run
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--group',
        required=True,
        help='Group display name (exact match)'
    )
    parser.add_argument(
        '--email',
        required=True,
        help='User email address to add to the group'
    )
    
    # Optional arguments
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging to see full request/response details'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making actual changes'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Check for credentials
    if not os.getenv("SCIM_BASE_URL") or not os.getenv("SCIM_TOKEN"):
        print("ERROR: SCIM credentials not found!")
        print("Please set SCIM_BASE_URL and SCIM_TOKEN environment variables")
        print("or create a .env file with these values.")
        print("See .env.example for the required format.")
        return 1
    
    try:
        client = SCIMClient()
        
        print("🎯 Adding user to group")
        print(f"  Group Name: {args.group}")
        print(f"  User Email: {args.email}")
        print()
        
        # Find the user
        user = find_user_by_email(client, args.email)
        if not user:
            return 1
        
        # Find the group
        group = find_group_by_name(client, args.group)
        if not group:
            return 1
        
        user_id = user.get('id')
        group_id = group.get('id')
        user_name = user.get('userName')
        
        print()
        
        # Check if user is already in the group
        if is_user_in_group(group, user_id):
            print(f"ℹ️  User '{user_name}' is already a member of group '{args.group}'")
            return 0
        
        # Prepare updated group data using PUT (full replacement)
        current_members = group.get('members', [])
        new_member = {
            "value": user_id,
            "display": user_name
        }
        
        updated_members = current_members + [new_member]
        
        # Create complete group data for PUT operation
        updated_group_data = {
            "schemas": group.get("schemas", ["urn:ietf:params:scim:schemas:core:2.0:Group"]),
            #"id": group_id,
            "displayName": group.get('displayName'),
            "members": updated_members
        }
        
        # Preserve any other group attributes
        for key, value in group.items():
            if key not in ['schemas', 'id', 'displayName', 'members', 'meta', 'created', 'lastModified']:
                updated_group_data[key] = value
        
        print("📋 Summary:")
        print(f"  User: {user_name} (ID: {user_id})")
        print(f"  Group: {args.group} (ID: {group_id})")
        print(f"  Current members: {len(current_members)}")
        print(f"  After addition: {len(updated_members)}")
        print(f"  Operation: PUT (full group replacement)")
        print()
        
        if args.dry_run:
            print("DRY RUN: Would add user to group (no actual API call made)")
            print("Updated group data would be:")
            print(json.dumps(updated_group_data, indent=2))
            return 0
        
        # Confirmation (unless --force is used)
        if not args.force:
            confirm = input(f"Add user '{user_name}' to group '{args.group}'? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("Operation cancelled.")
                return 0
        
        print("Adding user to group using PUT operation...")
        
        # Use PUT to update the entire group
        response = client.update_group(group_id, updated_group_data)
        
        if response.status_code == 200:
            updated_group = response.json()
            updated_member_count = len(updated_group.get('members', []))
            
            print("✅ User successfully added to group!")
            print(f"  Group now has {updated_member_count} members")
            return 0
        
        else:
            print(f"❌ Failed to add user to group!")
            print(f"Status Code: {response.status_code}")
            
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error Response: {response.text}")
            
            return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(add_user_to_group_cli())