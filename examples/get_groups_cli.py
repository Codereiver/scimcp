#!/usr/bin/env python3
"""
CLI tool for retrieving groups via SCIM API.

This script allows you to retrieve groups from the SCIM endpoint with support
for pagination, filtering, and pretty-printed JSON output.

Usage:
    python examples/get_groups_cli.py
    python examples/get_groups_cli.py --count 50
    python examples/get_groups_cli.py --filter 'displayName sw "Admin"'
    python examples/get_groups_cli.py --start-index 11 --count 10
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


def get_groups_cli():
    """Get groups via command line interface."""
    parser = argparse.ArgumentParser(
        description='Retrieve groups via Cato Networks SCIM API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --count 50
  %(prog)s --start-index 11 --count 10
  %(prog)s --filter 'displayName sw "Admin"'
  %(prog)s --filter 'displayName co "Department"'
  %(prog)s --filter 'members pr'
  %(prog)s --summary
  %(prog)s --debug

SCIM Filter Examples:
  displayName sw "Admin"       - Group name starts with "Admin"
  displayName co "Dept"        - Group name contains "Dept"
  displayName eq "Managers"    - Exact group name match
  members pr                   - Groups that have members
        """
    )
    
    # Optional arguments
    parser.add_argument(
        '--count',
        type=int,
        default=100,
        help='Number of groups to return (max 100, default: 100)'
    )
    parser.add_argument(
        '--start-index',
        type=int,
        default=1,
        help='Starting index for pagination (1-based, default: 1)'
    )
    parser.add_argument(
        '--filter',
        help='SCIM filter expression (e.g., \'displayName sw "Admin"\')'
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
        
        print("🔍 Retrieving groups...")
        print(f"  Start Index: {args.start_index}")
        print(f"  Count: {args.count}")
        if args.filter:
            print(f"  Filter: {args.filter}")
        print()
        
        # Get groups
        response = client.get_groups(
            start_index=args.start_index,
            count=args.count,
            filter_expr=args.filter
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to retrieve groups!")
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
        print(f"  Retrieved: {len(resources)} groups")
        print()
        
        if args.summary:
            # Show summary table
            if resources:
                print("📋 Group Summary:")
                print(f"{'ID':<20} {'Display Name':<40} {'Members':<8}")
                print("-" * 68)
                
                for group in resources:
                    group_id = group.get('id', 'N/A')[:19]
                    display_name = group.get('displayName', 'N/A')[:39]
                    
                    members = group.get('members', [])
                    member_count = len(members) if members else 0
                    
                    print(f"{group_id:<20} {display_name:<40} {member_count:<8}")
                
                # Show detailed member information if requested
                print()
                for i, group in enumerate(resources):
                    members = group.get('members', [])
                    if members:
                        print(f"📁 Group '{group.get('displayName', 'N/A')}' members:")
                        for member in members[:5]:  # Show first 5 members
                            member_display = member.get('display', 'N/A')
                            member_value = member.get('value', 'N/A')[:10] + '...' if len(member.get('value', '')) > 10 else member.get('value', 'N/A')
                            print(f"   • {member_display} (ID: {member_value})")
                        
                        if len(members) > 5:
                            print(f"   ... and {len(members) - 5} more members")
                        print()
            else:
                print("No groups found.")
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
    sys.exit(get_groups_cli())