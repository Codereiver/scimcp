#!/usr/bin/env python3
"""
CLI tool for deleting users via SCIM API.

This script allows you to delete a user by providing their user ID via 
command line arguments. For safety, it will show user details before 
deletion and require confirmation.

Usage:
    python examples/delete_user_cli.py --user-id 12345
    python examples/delete_user_cli.py --user-id 12345 --force
    python examples/delete_user_cli.py --user-id 12345 --debug
"""

import sys
import os
import argparse
import logging

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


def delete_user_cli():
    """Delete user via command line interface."""
    parser = argparse.ArgumentParser(
        description='Delete a user via Cato Networks SCIM API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --user-id 12345
  %(prog)s --user-id 67890 --force
  %(prog)s --user-id abcdef --debug
  %(prog)s --user-id 12345 --dry-run
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--user-id',
        required=True,
        help='SCIM User ID to delete'
    )
    
    # Optional arguments
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt (dangerous!)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging to see full request/response details'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show user details without actually deleting'
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
        
        print(f"Looking up user with ID: {args.user_id}")
        print()
        
        # First, get the user to show details before deletion
        response = client.get_user(args.user_id)
        
        if response.status_code == 404:
            print(f"❌ User with ID '{args.user_id}' not found.")
            return 1
        elif response.status_code != 200:
            print(f"❌ Failed to retrieve user details!")
            print(f"Status Code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error Response: {response.text}")
            return 1
        
        # Show user details
        user = response.json()
        print("📋 User Details:")
        print(f"  User ID: {user.get('id')}")
        print(f"  Username: {user.get('userName')}")
        print(f"  External ID: {user.get('externalId', 'N/A')}")
        
        name = user.get('name', {})
        if name:
            full_name = f"{name.get('givenName', '')} {name.get('familyName', '')}".strip()
            print(f"  Full Name: {full_name or 'N/A'}")
        
        emails = user.get('emails', [])
        if emails:
            primary_email = next((email['value'] for email in emails if email.get('primary')), emails[0]['value'] if emails else 'N/A')
            print(f"  Email: {primary_email}")
        
        print(f"  Active: {user.get('active', 'N/A')}")
        
        # Show creation/modification dates if available
        meta = user.get('meta', {})
        if meta.get('created'):
            print(f"  Created: {meta['created']}")
        if meta.get('lastModified'):
            print(f"  Last Modified: {meta['lastModified']}")
        
        print()
        
        if args.dry_run:
            print("DRY RUN: Would delete the above user (no actual API call made)")
            return 0
        
        # Confirmation (unless --force is used)
        if not args.force:
            print("⚠️  WARNING: This action cannot be undone!")
            confirm = input(f"Are you sure you want to DELETE user '{user.get('userName')}'? (type 'DELETE' to confirm): ").strip()
            if confirm != 'DELETE':
                print("User deletion cancelled.")
                return 0
        
        print("Deleting user...")
        
        # Delete the user
        delete_response = client.delete_user(args.user_id)
        
        if delete_response.status_code in [200, 204]:
            print("✅ User deleted successfully!")
            return 0
        
        else:
            print(f"❌ Failed to delete user!")
            print(f"Status Code: {delete_response.status_code}")
            
            try:
                error_data = delete_response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error Response: {delete_response.text}")
            
            return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(delete_user_cli())