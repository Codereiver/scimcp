"""Test configuration and fixtures for SCIM wrapper tests."""

import pytest
import os
from unittest.mock import patch


@pytest.fixture
def mock_env_vars():
    """Fixture to provide mock environment variables."""
    return {
        "SCIM_BASE_URL": "https://api.example.com/scim/v2",
        "SCIM_TOKEN": "test-bearer-token-12345",
        "DEBUG": "false"
    }


@pytest.fixture
def clean_env():
    """Fixture to ensure clean environment variables for testing."""
    env_vars_to_clear = ["SCIM_BASE_URL", "SCIM_TOKEN", "DEBUG"]
    original_values = {}
    
    # Store original values
    for var in env_vars_to_clear:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def sample_scim_user():
    """Sample SCIM user data for testing."""
    return {
        "userName": "testuser@example.com",
        "name": {
            "givenName": "Test",
            "familyName": "User"
        },
        "emails": [
            {
                "value": "testuser@example.com",
                "primary": True
            }
        ],
        "active": True
    }


@pytest.fixture
def sample_scim_response():
    """Sample SCIM response data for testing."""
    return {
        "id": "12345",
        "userName": "testuser@example.com",
        "name": {
            "givenName": "Test",
            "familyName": "User"
        },
        "emails": [
            {
                "value": "testuser@example.com",
                "primary": True
            }
        ],
        "active": True,
        "meta": {
            "resourceType": "User",
            "created": "2023-01-01T00:00:00Z",
            "lastModified": "2023-01-01T00:00:00Z"
        }
    }