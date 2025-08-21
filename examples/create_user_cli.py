#!/usr/bin/env python3
"""
CLI tool for creating users via SCIM API.

This script allows you to create a new user by providing email, firstName, 
and lastName via command line arguments. The externalId and password will 
be automatically generated if not provided.

Usage:
    python examples/create_user_cli.py --email user@example.com --firstName John --lastName Doe
    python examples/create_user_cli.py --email user@example.com --firstName John --lastName Doe --externalId CUSTOM123
    python examples/create_user_cli.py --email user@example.com --firstName John --lastName Doe --password MyPassword123!
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


def create_user_cli():
    """Create user via command line interface."""
    parser = argparse.ArgumentParser(
        description='Create a new user via Cato Networks SCIM API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --email john.doe@company.com --firstName John --lastName Doe
  %(prog)s --email jane@company.com --firstName Jane --lastName Smith --externalId JANE001
  %(prog)s --email admin@company.com --firstName Admin --lastName User --password SecurePass123!
  %(prog)s --email test@company.com --firstName Test --lastName User --debug
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--email',
        required=True,
        help='User email address (will be used as userName)'
    )
    parser.add_argument(
        '--firstName',
        required=True,
        help='User first name'
    )
    parser.add_argument(
        '--lastName',
        required=True,
        help='User last name'
    )
    
    # Optional arguments
    parser.add_argument(
        '--externalId',
        help='External ID for the user (if not provided, will be auto-generated)'
    )
    parser.add_argument(
        '--password',
        help='User password (if not provided, will be auto-generated)'
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
        
        print("Creating new user with the following details:")
        print(f"  Email: {args.email}")
        print(f"  First Name: {args.firstName}")
        print(f"  Last Name: {args.lastName}")
        
        if args.externalId:
            print(f"  External ID: {args.externalId}")
        else:
            print("  External ID: [auto-generated]")
        
        if args.password:
            print("  Password: [custom provided]")
        else:
            print("  Password: [auto-generated easy-to-remember]")
        
        print()
        
        if args.dry_run:
            print("DRY RUN: Would create user with above details (no actual API call made)")
            print()
            
            # Generate the values that would be used
            external_id = args.externalId or client._generate_external_id()
            password = args.password or client._generate_easy_password()
            
            # Show the JSON payload that would be sent
            user_payload = {
                "schemas": [
                    "urn:ietf:params:scim:schemas:core:2.0:User"
                ],
                "userName": args.email,
                "externalId": external_id,
                "name": {
                    "givenName": args.firstName,
                    "familyName": args.lastName
                },
                "emails": [
                    {
                        "value": args.email,
                        "primary": True
                    }
                ],
                "password": password,
                "active": True
            }
            
            print("📄 JSON Request Payload:")
            print(json.dumps(user_payload, indent=2))
            return 0
        
        # Confirm before creating
        confirm = input("Do you want to create this user? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("User creation cancelled.")
            return 0
        
        print("Creating user...")
        
        # Create the user
        response = client.create_user(
            email=args.email,
            firstName=args.firstName,
            lastName=args.lastName,
            externalId=args.externalId,
            password=args.password
        )
        
        if response.status_code == 201:
            created_user = response.json()
            
            print("✅ User created successfully!")
            print(f"  User ID: {created_user.get('id')}")
            print(f"  Username: {created_user.get('userName')}")
            print(f"  External ID: {created_user.get('externalId')}")
            print(f"  Full Name: {created_user.get('name', {}).get('formatted', 'N/A')}")
            print(f"  Active: {created_user.get('active', 'N/A')}")
            
            if not args.password:
                # Try to extract password from debug logs or mention it was auto-generated
                print("  Password: [auto-generated - check debug logs if enabled]")
            
            return 0
        
        else:
            print(f"❌ Failed to create user!")
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
    sys.exit(create_user_cli())