"""Tests for SCIM client functionality."""

import pytest
import os
import json
import logging
from unittest.mock import Mock, patch, MagicMock
import requests

from scimcp.scim_client import SCIMClient


class TestSCIMClientInitialization:
    """Tests for SCIMClient initialization."""
    
    def test_init_with_parameters(self):
        """Test initialization with direct parameters."""
        client = SCIMClient(
            base_url="https://api.example.com/scim/v2",
            token="test-token"
        )
        
        assert client.base_url == "https://api.example.com/scim/v2"
        assert client.token == "test-token"
        assert client.headers["Authorization"] == "Bearer test-token"
        assert client.headers["Content-Type"] == "application/scim+json"
        assert client.headers["Accept"] == "application/scim+json"
    
    def test_init_with_env_vars(self, clean_env, mock_env_vars):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, mock_env_vars):
            client = SCIMClient()
            
            assert client.base_url == "https://api.example.com/scim/v2"
            assert client.token == "test-bearer-token-12345"
            assert client.headers["Authorization"] == "Bearer test-bearer-token-12345"
    
    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from base URL."""
        client = SCIMClient(
            base_url="https://api.example.com/scim/v2/",
            token="test-token"
        )
        
        assert client.base_url == "https://api.example.com/scim/v2"
    
    def test_init_missing_base_url_raises_error(self, clean_env):
        """Test that missing base URL raises ValueError."""
        with pytest.raises(ValueError, match="SCIM base URL must be provided"):
            SCIMClient(token="test-token")
    
    def test_init_missing_token_raises_error(self, clean_env):
        """Test that missing token raises ValueError."""
        with pytest.raises(ValueError, match="SCIM token must be provided"):
            SCIMClient(base_url="https://api.example.com/scim/v2")
    
    def test_debug_flag_from_env_var(self, clean_env):
        """Test debug flag configuration from environment variable."""
        test_cases = [
            ("true", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("", False)
        ]
        
        for debug_value, expected in test_cases:
            env_vars = {
                "SCIM_BASE_URL": "https://api.example.com/scim/v2",
                "SCIM_TOKEN": "test-token",
                "DEBUG": debug_value
            }
            
            with patch.dict(os.environ, env_vars, clear=True):
                client = SCIMClient()
                assert client.debug == expected


class TestSCIMClientRequests:
    """Tests for SCIM client HTTP request functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return SCIMClient(
            base_url="https://api.example.com/scim/v2",
            token="test-token"
        )
    
    @patch('scimcp.scim_client.requests.request')
    def test_make_request_basic(self, mock_request, client):
        """Test basic HTTP request functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/scim+json"}
        mock_response.json.return_value = {"id": "123"}
        mock_request.return_value = mock_response
        
        response = client._make_request("GET", "/Users/123")
        
        mock_request.assert_called_once_with(
            method="GET",
            url="https://api.example.com/scim/v2/Users/123",
            headers=client.headers,
            json=None,
            timeout=30
        )
        assert response == mock_response
    
    @patch('scimcp.scim_client.requests.request')
    def test_make_request_with_payload(self, mock_request, client, sample_scim_user):
        """Test HTTP request with JSON payload."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/scim+json"}
        mock_response.json.return_value = {"id": "123"}
        mock_request.return_value = mock_response
        
        response = client._make_request("POST", "/Users", sample_scim_user)
        
        mock_request.assert_called_once_with(
            method="POST",
            url="https://api.example.com/scim/v2/Users",
            headers=client.headers,
            json=sample_scim_user,
            timeout=30
        )
        assert response == mock_response
    
    @patch('scimcp.scim_client.requests.request')
    def test_make_request_strips_leading_slash(self, mock_request, client):
        """Test that leading slash is handled correctly in endpoint."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {}
        mock_request.return_value = mock_response
        
        client._make_request("GET", "/Users")
        client._make_request("GET", "Users")
        
        # Both calls should result in the same URL
        assert mock_request.call_count == 2
        for call in mock_request.call_args_list:
            assert call[1]['url'] == "https://api.example.com/scim/v2/Users"


class TestSCIMClientLogging:
    """Tests for SCIM client debug logging functionality."""
    
    @pytest.fixture
    def client_with_debug(self, clean_env):
        """Create a test client with debug enabled."""
        env_vars = {
            "SCIM_BASE_URL": "https://api.example.com/scim/v2",
            "SCIM_TOKEN": "test-token",
            "DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            return SCIMClient()
    
    @pytest.fixture
    def client_without_debug(self, clean_env):
        """Create a test client with debug disabled."""
        env_vars = {
            "SCIM_BASE_URL": "https://api.example.com/scim/v2",
            "SCIM_TOKEN": "test-token",
            "DEBUG": "false"
        }
        
        with patch.dict(os.environ, env_vars):
            return SCIMClient()
    
    @patch('scimcp.scim_client.requests.request')
    def test_debug_logging_enabled(self, mock_request, client_with_debug, sample_scim_user, caplog):
        """Test that debug logging works when enabled."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/scim+json"}
        mock_response.json.return_value = {"id": "123", "userName": "test"}
        mock_request.return_value = mock_response
        
        with caplog.at_level(logging.DEBUG):
            client_with_debug._make_request("POST", "/Users", sample_scim_user)
        
        # Check that debug messages were logged
        debug_messages = [record.message for record in caplog.records if record.levelno == logging.DEBUG]
        
        assert any("=== SCIM REQUEST ===" in msg for msg in debug_messages)
        assert any("=== SCIM RESPONSE ===" in msg for msg in debug_messages)
        assert any("Method: POST" in msg for msg in debug_messages)
        assert any("Status Code: 201" in msg for msg in debug_messages)
    
    @patch('scimcp.scim_client.requests.request')
    def test_debug_logging_disabled(self, mock_request, client_without_debug, sample_scim_user, caplog):
        """Test that debug logging is disabled when DEBUG is false."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/scim+json"}
        mock_response.json.return_value = {"id": "123"}
        mock_request.return_value = mock_response
        
        with caplog.at_level(logging.DEBUG):
            client_without_debug._make_request("POST", "/Users", sample_scim_user)
        
        # Check that no debug messages were logged
        debug_messages = [record.message for record in caplog.records if record.levelno == logging.DEBUG]
        assert not any("=== SCIM REQUEST ===" in msg for msg in debug_messages)
        assert not any("=== SCIM RESPONSE ===" in msg for msg in debug_messages)
    
    @patch('scimcp.scim_client.requests.request')
    def test_debug_logging_handles_non_json_response(self, mock_request, client_with_debug, caplog):
        """Test that debug logging handles non-JSON responses gracefully."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response
        
        with caplog.at_level(logging.DEBUG):
            client_with_debug._make_request("GET", "/Users")
        
        debug_messages = [record.message for record in caplog.records if record.levelno == logging.DEBUG]
        assert any("Response Body (raw): Internal Server Error" in msg for msg in debug_messages)
    
    def test_log_request_response_pretty_prints_json(self, client_with_debug, caplog):
        """Test that JSON payloads are pretty printed in debug logs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/scim+json"}
        mock_response.json.return_value = {"id": "123", "userName": "test"}
        
        payload = {"userName": "test", "active": True}
        
        with caplog.at_level(logging.DEBUG):
            client_with_debug._log_request_response("POST", "https://api.example.com/Users", payload, mock_response)
        
        # Check that JSON is pretty printed (contains newlines and indentation)
        payload_logs = [msg for msg in caplog.messages if "Payload:" in msg]
        assert len(payload_logs) > 0
        assert "{\n" in payload_logs[0]  # Pretty printed JSON should have newlines


class TestSCIMClientUserCreation:
    """Tests for SCIM client user creation functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return SCIMClient(
            base_url="https://api.example.com/scim/v2",
            token="test-token"
        )
    
    @patch('scimcp.scim_client.requests.request')
    def test_create_user_with_all_parameters(self, mock_request, client):
        """Test creating user with all parameters provided."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/scim+json"}
        mock_response.json.return_value = {"id": "123", "userName": "test@example.com"}
        mock_request.return_value = mock_response
        
        response = client.create_user(
            email="test@example.com",
            firstName="Test",
            lastName="User",
            externalId="custom-id",
            password="CustomPass123!"
        )
        
        # Verify the request
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        
        assert call_args[1]['method'] == "POST"
        assert call_args[1]['url'] == "https://api.example.com/scim/v2/Users"
        
        user_data = call_args[1]['json']
        assert user_data['userName'] == "test@example.com"
        assert user_data['externalId'] == "custom-id"
        assert user_data['password'] == "CustomPass123!"
        assert user_data['name']['givenName'] == "Test"
        assert user_data['name']['familyName'] == "User"
        assert user_data['emails'][0]['value'] == "test@example.com"
        assert user_data['emails'][0]['primary'] is True
        assert user_data['active'] is True
    
    @patch('scimcp.scim_client.requests.request')
    def test_create_user_generates_external_id(self, mock_request, client):
        """Test that external ID is generated when not provided."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/scim+json"}
        mock_response.json.return_value = {"id": "123"}
        mock_request.return_value = mock_response
        
        response = client.create_user(
            email="test@example.com",
            firstName="Test",
            lastName="User"
        )
        
        user_data = mock_request.call_args[1]['json']
        
        # Check that external ID was generated (12 characters)
        assert 'externalId' in user_data
        assert len(user_data['externalId']) == 12
        assert user_data['externalId'].isalnum()
    
    @patch('scimcp.scim_client.requests.request')
    def test_create_user_generates_password(self, mock_request, client):
        """Test that password is generated when not provided."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/scim+json"}
        mock_response.json.return_value = {"id": "123"}
        mock_request.return_value = mock_response
        
        response = client.create_user(
            email="test@example.com",
            firstName="Test",
            lastName="User"
        )
        
        user_data = mock_request.call_args[1]['json']
        
        # Check that password was generated and follows expected pattern
        assert 'password' in user_data
        password = user_data['password']
        assert len(password) > 6  # Should be reasonably long
        assert password.endswith('!')  # Should end with !
        # Should contain letters and numbers
        assert any(c.isalpha() for c in password)
        assert any(c.isdigit() for c in password)
    
    def test_generate_external_id_format(self, client):
        """Test external ID generation format."""
        external_id = client._generate_external_id()
        
        assert len(external_id) == 12
        assert external_id.isalnum()
        
        # Test multiple generations are different
        external_id2 = client._generate_external_id()
        assert external_id != external_id2  # Very unlikely to be the same
    
    def test_generate_easy_password_format(self, client):
        """Test easy password generation format."""
        password = client._generate_easy_password()
        
        assert len(password) > 6
        assert password.endswith('!')
        assert any(c.isalpha() for c in password)
        assert any(c.isdigit() for c in password)
        
        # Test multiple generations
        password2 = client._generate_easy_password()
        assert isinstance(password2, str)
        assert password2.endswith('!')