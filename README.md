# SCIMCP - MCP Server for Cato Networks SCIM API

> ⚠️ **DISCLAIMER**: This is an unofficial, community-developed tool and is NOT an official Cato Networks release. It is not affiliated with, endorsed by, or supported by Cato Networks. Use at your own risk.

A Model Context Protocol (MCP) server that provides SCIM (System for Cross-domain Identity Management) tools for managing users and groups in Cato Networks. This allows LLMs to interact with Cato Networks' identity management system through a standardized protocol.

## Features

- **Full SCIM User Management**: Create, read, update, and delete users
- **Full SCIM Group Management**: Create, read, update, and delete groups
- **MCP Protocol Support**: Expose SCIM operations as MCP tools for LLM consumption
- **Docker Support**: Run as a containerized service for easy deployment
- **Auto-generation**: Automatic generation of external IDs and passwords
- **CLI Tools**: Command-line interfaces for direct user and group creation
- **Comprehensive Testing**: Unit tests and integration examples

## Table of Contents

- [Installation](#installation)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Python Client](#python-client)
  - [CLI Tools](#cli-tools)
  - [MCP Server](#mcp-server)
- [Docker](#docker)
  - [Building the Image](#building-the-image)
  - [Running with Docker Compose](#running-with-docker-compose)
  - [Running Standalone](#running-standalone)
- [MCP Integration](#mcp-integration)
- [API Reference](#api-reference)
- [Testing](#testing)
- [License](#license)

## Installation

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/scimcp.git
cd scimcp
```

2. **Install dependencies:**
```bash
# Basic dependencies
pip install -r requirements.txt

# Development dependencies (includes pytest)
pip install -r requirements-dev.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your Cato Networks SCIM credentials
```

### Docker Deployment

For production deployment, use Docker:

```bash
# Build the image
docker build -t scimcp:latest .

# Or use docker-compose
docker-compose up -d
```

## Configuration

The application uses environment variables for configuration. Create a `.env` file:

```env
# Required: Cato Networks SCIM API credentials
SCIM_BASE_URL=https://api.catonetworks.com/api/v1/scim/v2.0
SCIM_TOKEN=your-bearer-token-here

# Optional: Enable debug logging
DEBUG=false
```

## Usage

### Python Client

The `SCIMClient` class provides a simple interface for SCIM operations:

```python
from scimcp import SCIMClient

# Initialize client (reads from environment or .env file)
client = SCIMClient()

# Create a user (auto-generates externalId and password)
response = client.create_user(
    email="john.doe@example.com",
    firstName="John",
    lastName="Doe"
)

# Create a group (auto-generates 8-digit externalId)
response = client.create_group(displayName="Engineering Team")

# List users with filtering
response = client.get_users(filter_expr='userName sw "john"')

# Get specific user
response = client.get_user(user_id="12345")

# Update a group (e.g., rename) - MUST include externalId
group_response = client.get_group(group_id="67890")
group_data = group_response.json()
group_data["displayName"] = "New Engineering Team Name"
# IMPORTANT: Keep the externalId when updating
update_response = client.update_group(group_id="67890", group_data=group_data)

# Add users to a group
response = client.add_members_to_group(
    group_id="67890",
    user_ids=["user123", "user456", "user789"]
)

# Remove users from a group
response = client.remove_members_from_group(
    group_id="67890",
    user_ids=["user456"]
)
```

### CLI Tools

Command-line tools for quick operations:

```bash
# Create a user
python examples/create_user_cli.py \
    --email john.doe@example.com \
    --firstName John \
    --lastName Doe

# Create a group
python examples/create_group_cli.py \
    --displayName "Engineering Team"

# With custom external ID
python examples/create_group_cli.py \
    --displayName "Sales Team" \
    --externalId SALES001

# Dry run to preview
python examples/create_user_cli.py \
    --email test@example.com \
    --firstName Test \
    --lastName User \
    --dry-run
```

### MCP Server

The MCP server exposes SCIM operations as tools:

```bash
# Run directly
python -m scimcp.mcp_server

# Or with Docker
docker run -e SCIM_BASE_URL=$SCIM_BASE_URL -e SCIM_TOKEN=$SCIM_TOKEN scimcp:latest
```

## Docker

### Building the Image

Build the Docker image locally:

```bash
# Standard build
docker build -t scimcp:latest .

# Multi-platform build (for ARM and x86)
docker buildx build --platform linux/amd64,linux/arm64 -t scimcp:latest .

# With specific version tag
docker build -t scimcp:1.0.0 .
```

### Running with Docker Compose

The easiest way to run the MCP server:

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f scimcp

# Stop the service
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Running Standalone

Run the container directly:

```bash
# Basic run
docker run -d \
  --name scimcp-server \
  -e SCIM_BASE_URL="https://api.catonetworks.com/api/v1/scim/v2.0" \
  -e SCIM_TOKEN="your-token-here" \
  scimcp:latest

# With resource limits
docker run -d \
  --name scimcp-server \
  -e SCIM_BASE_URL="$SCIM_BASE_URL" \
  -e SCIM_TOKEN="$SCIM_TOKEN" \
  --memory="256m" \
  --cpus="0.5" \
  scimcp:latest

# Interactive mode for debugging
docker run -it --rm \
  -e SCIM_BASE_URL="$SCIM_BASE_URL" \
  -e SCIM_TOKEN="$SCIM_TOKEN" \
  -e DEBUG=true \
  scimcp:latest
```

## MCP Integration

### Available Tools

The MCP server provides the following tools:

#### User Management
- `scim_list_users` - List or search users with optional filtering
- `scim_get_user` - Get a specific user by ID
- `scim_create_user` - Create a new user
- `scim_update_user` - Update an existing user (preserve externalId when updating)
- `scim_delete_user` - Delete a user

#### Group Management
- `scim_list_groups` - List or search groups with optional filtering
- `scim_get_group` - Get a specific group by ID
- `scim_create_group` - Create a new group
- `scim_update_group` - Update an existing group (**IMPORTANT**: Must include existing externalId when renaming)
- `scim_delete_group` - Delete a group
- `scim_add_users_to_group` - Add users to a group using PATCH operation
- `scim_remove_users_from_group` - Remove users from a group using PATCH operation

#### Important Notes on Updates
When updating users or groups, especially when renaming:
- **Always include the existing `externalId`** in the update payload to preserve it
- The update operation replaces the entire resource, so include all fields you want to keep
- For group renaming: First fetch the group, then update with both new `displayName` and existing `externalId`

### MCP Client Configuration

To use this MCP server with an LLM client, add it to your MCP configuration:

```json
{
  "mcpServers": {
    "scimcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", 
               "-e", "SCIM_BASE_URL=https://api.catonetworks.com/api/v1/scim/v2.0",
               "-e", "SCIM_TOKEN=your-token-here",
               "scimcp:latest"]
    }
  }
}
```

Or for local development:

```json
{
  "mcpServers": {
    "scimcp": {
      "command": "python",
      "args": ["-m", "scimcp.mcp_server"],
      "env": {
        "SCIM_BASE_URL": "https://api.catonetworks.com/api/v1/scim/v2.0",
        "SCIM_TOKEN": "your-token-here"
      }
    }
  }
}
```

## API Reference

### SCIMClient Methods

#### User Operations

- `get_users(filter_expr=None, start_index=1, count=100)` - List users
- `get_user(user_id)` - Get specific user
- `create_user(email, firstName, lastName, externalId=None, password=None)` - Create user
- `update_user(user_id, user_data)` - Update user
- `delete_user(user_id)` - Delete user

#### Group Operations

- `get_groups(filter_expr=None, start_index=1, count=100)` - List groups
- `get_group(group_id)` - Get specific group
- `create_group(displayName, externalId=None)` - Create group
- `update_group(group_id, group_data)` - Update group
- `delete_group(group_id)` - Delete group
- `add_members_to_group(group_id, user_ids)` - Add users to group
- `remove_members_from_group(group_id, user_ids)` - Remove users from group
- `patch_group(group_id, patch_operations)` - Apply PATCH operations to group

### Auto-generation Features

- **User External ID**: 12-character alphanumeric string
- **User Password**: Easy-to-remember format (Word-Word-Digits)
- **Group External ID**: 8-digit number

## Testing

Run the test suite:

```bash
# All tests
python -m pytest

# Unit tests only
python -m pytest tests/

# With coverage
python -m pytest --cov=scimcp tests/

# Integration tests (requires valid credentials)
python examples/integration_test.py

# Basic usage examples
python examples/basic_usage.py
```

## Project Structure

```
scimcp/
├── scimcp/                     # Main package
│   ├── __init__.py
│   ├── scim_client.py          # SCIM client implementation
│   └── mcp_server.py           # MCP server implementation
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── conftest.py             # Test fixtures
│   └── test_scim_client.py     # Client tests
├── examples/                   # Usage examples
│   ├── integration_test.py     # Integration tests
│   ├── basic_usage.py          # Usage examples
│   ├── create_user_cli.py      # User creation CLI
│   └── create_group_cli.py     # Group creation CLI
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Docker Compose configuration
├── LICENSE                     # Apache 2.0 license
├── README.md                   # This file
├── requirements.txt            # Python dependencies
└── requirements-dev.txt        # Development dependencies
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify your SCIM token is valid
   - Check the SCIM_BASE_URL is correct
   - Ensure the token has necessary permissions

2. **Docker Build Failures**
   - Ensure Docker is installed and running
   - Check available disk space
   - Try building with `--no-cache` flag

3. **MCP Connection Issues**
   - Verify the container is running: `docker ps`
   - Check logs: `docker logs scimcp-server`
   - Ensure environment variables are set correctly

### Debug Mode

Enable debug logging to see detailed request/response information:

```bash
# Environment variable
export DEBUG=true

# Or in .env file
DEBUG=true

# Or when running Docker
docker run -e DEBUG=true ...
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please:
- Open an issue on GitHub
- Check existing documentation
- Review the examples directory

## Acknowledgments

- Cato Networks for providing the SCIM API
- MCP protocol by Anthropic for standardized LLM tool integration