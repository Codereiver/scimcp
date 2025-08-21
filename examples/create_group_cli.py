#!/usr/bin/env python3
"""
CLI tool for creating groups via SCIM API.

This script allows you to create a new group by providing the displayName 
via command line arguments. The externalId will be automatically generated 
as a random 8-digit number if not provided.

Usage:
    python examples/create_group_cli.py --displayName "Engineering Team"
    python examples/create_group_cli.py --displayName "Sales Team" --externalId GRP12345
    python examples/create_group_cli.py --displayName "Support Team" --debug
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


def create_group_cli():
    """Create group via command line interface."""
    parser = argparse.ArgumentParser(
        description='Create a new group via Cato Networks SCIM API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --displayName "Engineering Team"
  %(prog)s --displayName "Sales Team" --externalId SALES001
  %(prog)s --displayName "Marketing Team" --externalId MKT12345
  %(prog)s --displayName "Support Team" --debug
  %(prog)s --displayName "Test Group" --dry-run
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--displayName',
        required=True,
        help='Group display name'
    )
    
    # Optional arguments
    parser.add_argument(
        '--externalId',
        help='External ID for the group (if not provided, will be auto-generated 8-digit number)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging to see full request/response details'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without actually making the API call'
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
        
        print("Creating new group with the following details:")
        print(f"  Display Name: {args.displayName}")
        
        if args.externalId:
            print(f"  External ID: {args.externalId}")
        else:
            print("  External ID: [auto-generated 8-digit number]")
        
        print()
        
        if args.dry_run:
            print("DRY RUN: Would create group with above details (no actual API call made)")
            print()
            
            # Generate the values that would be used
            import random
            external_id = args.externalId or str(random.randint(10000000, 99999999))
            
            # Show the JSON payload that would be sent
            group_payload = {
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:Group"
                ],
                "displayName": args.displayName,
                "externalId": external_id
            }
            
            print("📄 JSON Request Payload:")
            print(json.dumps(group_payload, indent=2))
            
            if not args.externalId:
                print(f"\nGenerated External ID: {external_id}")
            
            return 0
        
        # Confirm before creating
        confirm = input("Do you want to create this group? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Group creation cancelled.")
            return 0
        
        print("Creating group...")
        
        # Create the group
        response = client.create_group(
            displayName=args.displayName,
            externalId=args.externalId
        )
        
        if response.status_code == 201:
            created_group = response.json()
            
            print("✅ Group created successfully!")
            print(f"  Group ID: {created_group.get('id')}")
            print(f"  Display Name: {created_group.get('displayName')}")
            print(f"  External ID: {created_group.get('externalId')}")
            
            # Display member count if available
            members = created_group.get('members', [])
            print(f"  Members: {len(members)}")
            
            # Display metadata if available
            meta = created_group.get('meta', {})
            if meta:
                print(f"  Created: {meta.get('created', 'N/A')}")
                print(f"  Resource Type: {meta.get('resourceType', 'N/A')}")
            
            return 0
        
        else:
            print(f"❌ Failed to create group!")
            print(f"Status Code: {response.status_code}")
            
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Error Response: {response.text}")
            
            return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(create_group_cli())