#!/usr/bin/env python3
"""
MCP Server for Cato Networks SCIM API.

This server exposes SCIM operations as MCP tools that can be used by LLMs
to manage users and groups in Cato Networks.
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Add parent directory to path to import scimcp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scimcp import SCIMClient


class SCIMMCPServer:
    """MCP Server wrapper for SCIM operations."""
    
    def __init__(self):
        self.server = Server("scimcp")
        self.client = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available SCIM tools."""
            return [
                types.Tool(
                    name="scim_list_users",
                    description="List or search users in Cato Networks SCIM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "SCIM filter expression (e.g., 'userName sw \"john\"')"
                            },
                            "start_index": {
                                "type": "integer",
                                "description": "Starting index for pagination (default: 1)"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of results per page (max: 100)"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="scim_get_user",
                    description="Get a specific user by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The SCIM user ID"
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                types.Tool(
                    name="scim_create_user",
                    description="Create a new user in Cato Networks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "User's email address (used as userName)"
                            },
                            "first_name": {
                                "type": "string",
                                "description": "User's first name"
                            },
                            "last_name": {
                                "type": "string",
                                "description": "User's last name"
                            },
                            "external_id": {
                                "type": "string",
                                "description": "External ID (auto-generated if not provided)"
                            },
                            "password": {
                                "type": "string",
                                "description": "User password (auto-generated if not provided)"
                            }
                        },
                        "required": ["email", "first_name", "last_name"]
                    }
                ),
                types.Tool(
                    name="scim_update_user",
                    description="Update an existing user. IMPORTANT: Include all fields you want to preserve, especially externalId.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The SCIM user ID"
                            },
                            "user_data": {
                                "type": "object",
                                "description": "SCIM user data to update. Should include 'externalId' field with the existing value to preserve it. Include all fields you want to keep or update."
                            }
                        },
                        "required": ["user_id", "user_data"]
                    }
                ),
                types.Tool(
                    name="scim_delete_user",
                    description="Delete a user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The SCIM user ID"
                            }
                        },
                        "required": ["user_id"]
                    }
                ),
                types.Tool(
                    name="scim_list_groups",
                    description="List or search groups in Cato Networks SCIM",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filter": {
                                "type": "string",
                                "description": "SCIM filter expression"
                            },
                            "start_index": {
                                "type": "integer",
                                "description": "Starting index for pagination (default: 1)"
                            },
                            "count": {
                                "type": "integer",
                                "description": "Number of results per page (max: 100)"
                            }
                        }
                    }
                ),
                types.Tool(
                    name="scim_get_group",
                    description="Get a specific group by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "The SCIM group ID"
                            }
                        },
                        "required": ["group_id"]
                    }
                ),
                types.Tool(
                    name="scim_create_group",
                    description="Create a new group in Cato Networks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "display_name": {
                                "type": "string",
                                "description": "Group display name"
                            },
                            "external_id": {
                                "type": "string",
                                "description": "External ID (auto-generated 8-digit number if not provided)"
                            }
                        },
                        "required": ["display_name"]
                    }
                ),
                types.Tool(
                    name="scim_update_group",
                    description="Update an existing group. IMPORTANT: When renaming a group, you MUST include the existing externalId in the group_data to preserve it.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "The SCIM group ID"
                            },
                            "group_data": {
                                "type": "object",
                                "description": "SCIM group data to update. MUST include 'externalId' field with the existing value when updating displayName to preserve the external ID. Include all fields you want to keep or update."
                            }
                        },
                        "required": ["group_id", "group_data"]
                    }
                ),
                types.Tool(
                    name="scim_delete_group",
                    description="Delete a group",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "The SCIM group ID"
                            }
                        },
                        "required": ["group_id"]
                    }
                ),
                types.Tool(
                    name="scim_add_users_to_group",
                    description="Add one or more users to a group using PATCH operation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "The SCIM group ID"
                            },
                            "user_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of SCIM user IDs to add to the group"
                            }
                        },
                        "required": ["group_id", "user_ids"]
                    }
                ),
                types.Tool(
                    name="scim_remove_users_from_group",
                    description="Remove one or more users from a group using PATCH operation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "group_id": {
                                "type": "string",
                                "description": "The SCIM group ID"
                            },
                            "user_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of SCIM user IDs to remove from the group"
                            }
                        },
                        "required": ["group_id", "user_ids"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]]
        ) -> list[types.TextContent]:
            """Handle tool calls."""
            
            if not self.client:
                self.client = SCIMClient()
            
            try:
                result = await self._execute_tool(name, arguments or {})
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": str(e),
                        "tool": name,
                        "arguments": arguments
                    }, indent=2)
                )]
    
    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a SCIM tool."""
        
        # User operations
        if name == "scim_list_users":
            response = self.client.get_users(
                filter_expr=arguments.get("filter"),
                start_index=arguments.get("start_index", 1),
                count=arguments.get("count", 100)
            )
            return self._process_response(response)
        
        elif name == "scim_get_user":
            response = self.client.get_user(arguments["user_id"])
            return self._process_response(response)
        
        elif name == "scim_create_user":
            response = self.client.create_user(
                email=arguments["email"],
                firstName=arguments["first_name"],
                lastName=arguments["last_name"],
                externalId=arguments.get("external_id"),
                password=arguments.get("password")
            )
            return self._process_response(response)
        
        elif name == "scim_update_user":
            response = self.client.update_user(
                arguments["user_id"],
                arguments["user_data"]
            )
            return self._process_response(response)
        
        elif name == "scim_delete_user":
            response = self.client.delete_user(arguments["user_id"])
            return self._process_response(response)
        
        # Group operations
        elif name == "scim_list_groups":
            response = self.client.get_groups(
                filter_expr=arguments.get("filter"),
                start_index=arguments.get("start_index", 1),
                count=arguments.get("count", 100)
            )
            return self._process_response(response)
        
        elif name == "scim_get_group":
            response = self.client.get_group(arguments["group_id"])
            return self._process_response(response)
        
        elif name == "scim_create_group":
            response = self.client.create_group(
                displayName=arguments["display_name"],
                externalId=arguments.get("external_id")
            )
            return self._process_response(response)
        
        elif name == "scim_update_group":
            response = self.client.update_group(
                arguments["group_id"],
                arguments["group_data"]
            )
            return self._process_response(response)
        
        elif name == "scim_delete_group":
            response = self.client.delete_group(arguments["group_id"])
            return self._process_response(response)
        
        # Group membership operations
        elif name == "scim_add_users_to_group":
            response = self.client.add_members_to_group(
                arguments["group_id"],
                arguments["user_ids"]
            )
            return self._process_response(response)
        
        elif name == "scim_remove_users_from_group":
            response = self.client.remove_members_from_group(
                arguments["group_id"],
                arguments["user_ids"]
            )
            return self._process_response(response)
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    def _process_response(self, response) -> Dict[str, Any]:
        """Process SCIM API response."""
        result = {
            "status_code": response.status_code,
            "success": response.status_code < 400
        }
        
        try:
            result["data"] = response.json()
        except:
            result["data"] = response.text
        
        return result
    
    async def run(self):
        """Run the MCP server."""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="scimcp",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main():
    """Main entry point."""
    server = SCIMMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())