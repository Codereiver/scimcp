#!/usr/bin/env python3
"""
CLI tool for retrieving users via SCIM API.

This script allows you to retrieve users from the SCIM endpoint with support
for pagination, filtering, and pretty-printed JSON output.

Usage:
    python examples/get_users_cli.py
    python examples/get_users_cli.py --count 50
    python examples/get_users_cli.py --filter 'userName sw "test"'
    python examples/get_users_cli.py --start-index 11 --count 10
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


def get_users_cli():
    """Get users via command line interface."""
    parser = argparse.ArgumentParser(
        description='Retrieve users via Cato Networks SCIM API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --count 50
  %(prog)s --start-index 11 --count 10
  %(prog)s --filter 'userName sw "test"'
  %(prog)s --filter 'active eq true'
  %(prog)s --filter 'emails.value co "@company.com"'
  %(prog)s --summary
  %(prog)s --debug

SCIM Filter Examples:
  userName sw "john"           - Username starts with "john"
  active eq true               - Active users only
  active eq false              - Inactive users only
  emails.value co "@company"   - Emails containing "@company"
  name.givenName eq "John"     - First name equals "John"
        """
    )
    
    # Optional arguments
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of users to return (max 100, default: 100)'
    )
    parser.add_argument(
        '--start-index',
        type=int,
        default=1,
        help='Starting index for pagination (1-based, default: 1)'
    )
    parser.add_argument(
        '--filter',
        help='SCIM filter expression (e.g., \'userName sw "test"\')'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show only summary information instead of full JSON'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging to see full request/response details'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.count > 100:
        print("WARNING: Count limited to maximum of 100")
        args.count = 100
    
    if args.start_index < 1:
        print("ERROR: start-index must be 1 or greater")
        return 1
    
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
        
        print("🔍 Retrieving users...")
        print(f"  Start Index: {args.start_index}")
        print(f"  Count: {args.count}")
        if args.filter:
            print(f"  Filter: {args.filter}")
        print()
        
        # Get users
        response = client.get_users(
            start_index=args.start_index,
            count=args.count,
            filter_expr=args.filter
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to retrieve users!")
            print(f"Status Code: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error Response: {response.text}")
            return 1
        
        data = response.json()
        
        # Show summary information
        total_results = data.get('totalResults', 0)
        items_per_page = data.get('itemsPerPage', 0)
        start_index = data.get('startIndex', 1)
        resources = data.get('Resources', [])
        
        print("📊 Results Summary:")
        print(f"  Total Results: {total_results}")
        print(f"  Items Per Page: {items_per_page}")
        print(f"  Start Index: {start_index}")
        print(f"  Retrieved: {len(resources)} users")
        print()
        
        if args.summary:
            # Show summary table
            if resources:
                print("📋 User Summary:")
                print(f"{'ID':<20} {'Username':<30} {'Name':<25} {'Active':<8}")
                print("-" * 83)
                
                for user in resources:
                    user_id = user.get('id', 'N/A')[:19]
                    username = user.get('userName', 'N/A')[:29]
                    
                    name = user.get('name', {})
                    full_name = f"{name.get('givenName', '')} {name.get('familyName', '')}".strip()
                    if not full_name:
                        full_name = 'N/A'
                    full_name = full_name[:24]
                    
                    active = str(user.get('active', 'N/A'))
                    
                    print(f"{user_id:<20} {username:<30} {full_name:<25} {active:<8}")
            else:
                print("No users found.")
        else:
            # Show full JSON
            print("📄 Full Response Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Show pagination info if there are more results
        if total_results > start_index + len(resources) - 1:
            next_start = start_index + len(resources)
            remaining = total_results - (start_index + len(resources) - 1)
            print()
            print(f"💡 To get next page, use: --start-index {next_start} --count {min(remaining, 100)}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(get_users_cli())