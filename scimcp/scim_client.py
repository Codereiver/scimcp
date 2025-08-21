"""SCIM client for Cato Networks API."""

import os
import json
import logging
import requests
import random
import string
from typing import Optional, Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class SCIMClient:
    """Simple SCIM client for Cato Networks API with bearer authentication."""
    
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        """Initialize SCIM client.
        
        Args:
            base_url: SCIM API base URL. If None, reads from SCIM_BASE_URL env var.
            token: Bearer token. If None, reads from SCIM_TOKEN env var.
        """
        self.base_url = base_url or os.getenv("SCIM_BASE_URL")
        self.token = token or os.getenv("SCIM_TOKEN")
        
        if not self.base_url:
            raise ValueError("SCIM base URL must be provided via parameter or SCIM_BASE_URL environment variable")
        
        if not self.token:
            raise ValueError("SCIM token must be provided via parameter or SCIM_TOKEN environment variable")
        
        # Remove trailing slash from base_url
        self.base_url = self.base_url.rstrip("/")
        
        # Setup headers
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/scim+json",
            "Accept": "application/scim+json"
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.debug = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
        
    def _log_request_response(self, method: str, url: str, payload: Optional[Dict[Any, Any]], response: requests.Response):
        """Log request and response details when DEBUG is enabled."""
        if not self.debug:
            return
            
        self.logger.debug(f"=== SCIM REQUEST ===")
        self.logger.debug(f"Method: {method}")
        self.logger.debug(f"URL: {url}")
        self.logger.debug(f"Headers: {json.dumps(dict(self.headers), indent=2)}")
        
        if payload:
            self.logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        self.logger.debug(f"=== SCIM RESPONSE ===")
        self.logger.debug(f"Status Code: {response.status_code}")
        self.logger.debug(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        
        try:
            response_json = response.json()
            self.logger.debug(f"Response Body: {json.dumps(response_json, indent=2)}")
        except json.JSONDecodeError:
            self.logger.debug(f"Response Body (raw): {response.text}")
    
    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict[Any, Any]] = None) -> requests.Response:
        """Make HTTP request to SCIM API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        self._log_request_response(method, url, payload, response)
        
        return response
    
    def get_users(self, start_index: int = 1, count: int = 100, filter_expr: Optional[str] = None) -> requests.Response:
        """Get users from SCIM endpoint.
        
        Args:
            start_index: Starting index for pagination (1-based).
            count: Number of users to return (max 100).
            filter_expr: SCIM filter expression (optional).
            
        Returns:
            Response object with user data.
        """
        params = {
            "startIndex": start_index,
            "count": min(count, 100)
        }
        
        if filter_expr:
            params["filter"] = filter_expr
        
        endpoint = "Users"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint = f"Users?{query_string}"
        
        return self._make_request("GET", endpoint)
    
    def get_user(self, user_id: str) -> requests.Response:
        """Get a specific user by ID.
        
        Args:
            user_id: The SCIM user ID.
            
        Returns:
            Response object with user data.
        """
        return self._make_request("GET", f"Users/{user_id}")
    
    def _generate_external_id(self) -> str:
        """Generate a random 12-character external ID."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    def _generate_easy_password(self) -> str:
        """Generate an easy-to-remember password using word pattern."""
        # Expanded word lists for easy-to-remember passwords
        adjectives = [
            "Quick", "Happy", "Bright", "Smart", "Cool", "Fast", "Safe", "Good",
            "Blue", "Green", "Red", "Gold", "Silver", "Purple", "Orange", "Pink",
            "Bold", "Calm", "Warm", "Fresh", "Clean", "Sweet", "Sharp", "Smooth",
            "Strong", "Light", "Dark", "Soft", "Hard", "Tall", "Short", "Wide",
            "Deep", "High", "Low", "Rich", "Pure", "Fine", "Rare", "New"
        ]
        nouns = [
            "Cat", "Dog", "Bird", "Fish", "Star", "Moon", "Sun", "Tree",
            "Lion", "Tiger", "Bear", "Wolf", "Fox", "Hawk", "Eagle", "Dove",
            "Rose", "Lily", "Oak", "Pine", "River", "Lake", "Hill", "Rock",
            "Fire", "Wind", "Rain", "Snow", "Cloud", "Storm", "Wave", "Ocean",
            "House", "Tower", "Bridge", "Castle", "Garden", "Forest", "Valley", "Mountain"
        ]
        
        adjective = random.choice(adjectives)
        noun = random.choice(nouns)
        number = random.randint(100000, 999999)  # Random 6-digit integer
        
        return f"{adjective}{noun}{number}!"
    
    def create_user(self, email: str, firstName: str, lastName: str, 
                   externalId: Optional[str] = None, password: Optional[str] = None) -> requests.Response:
        """Create a new user.
        
        Args:
            email: User's email address (used as userName).
            firstName: User's first name.
            lastName: User's last name.
            externalId: External ID for the user. If None, generates random 12-char ID.
            password: User's password. If None, generates easy-to-remember password.
            
        Returns:
            Response object with created user data.
        """
        if not externalId:
            externalId = self._generate_external_id()
        
        if not password:
            password = self._generate_easy_password()
        
        user_data = {
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:User"
            ],
            "userName": email,
            "externalId": externalId,
            "name": {
                "givenName": firstName,
                "familyName": lastName
            },
            "emails": [
                {
                    "value": email,
                    "primary": True
                }
            ],
            "password": password,
            "active": True
        }
        
        return self._make_request("POST", "Users", user_data)
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> requests.Response:
        """Update an existing user.
        
        Args:
            user_id: The SCIM user ID.
            user_data: SCIM user data dictionary.
            
        Returns:
            Response object with updated user data.
        """
        return self._make_request("PUT", f"Users/{user_id}", user_data)
    
    def delete_user(self, user_id: str) -> requests.Response:
        """Delete a user.
        
        Args:
            user_id: The SCIM user ID.
            
        Returns:
            Response object (typically empty for successful deletion).
        """
        return self._make_request("DELETE", f"Users/{user_id}")
    
    def get_groups(self, start_index: int = 1, count: int = 100, filter_expr: Optional[str] = None) -> requests.Response:
        """Get groups from SCIM endpoint.
        
        Args:
            start_index: Starting index for pagination (1-based).
            count: Number of groups to return (max 100).
            filter_expr: SCIM filter expression (optional).
            
        Returns:
            Response object with group data.
        """
        params = {
            "startIndex": start_index,
            "count": min(count, 100)
        }
        
        if filter_expr:
            params["filter"] = filter_expr
        
        endpoint = "Groups"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint = f"Groups?{query_string}"
        
        return self._make_request("GET", endpoint)
    
    def get_group(self, group_id: str) -> requests.Response:
        """Get a specific group by ID.
        
        Args:
            group_id: The SCIM group ID.
            
        Returns:
            Response object with group data.
        """
        return self._make_request("GET", f"Groups/{group_id}")
    
    def create_group(self, displayName: str, externalId: str = None) -> requests.Response:
        """Create a new group.
        
        Args:
            displayName: Group's display name (required).
            externalId: External ID for the group. If None, generates random 8-digit number.
            
        Returns:
            Response object with created group data.
        """
        if not externalId:
            import random
            externalId = str(random.randint(10000000, 99999999))
        
        group_data = {
            "schemas": [
                "urn:ietf:params:scim:schemas:core:2.0:Group"
            ],
            "displayName": displayName,
            "externalId": externalId
        }
        
        return self._make_request("POST", "Groups", group_data)
    
    def update_group(self, group_id: str, group_data: Dict[str, Any]) -> requests.Response:
        """Update an existing group.
        
        Args:
            group_id: The SCIM group ID.
            group_data: SCIM group data dictionary.
            
        Returns:
            Response object with updated group data.
        """
        return self._make_request("PUT", f"Groups/{group_id}", group_data)
    
    def delete_group(self, group_id: str) -> requests.Response:
        """Delete a group.
        
        Args:
            group_id: The SCIM group ID.
            
        Returns:
            Response object (typically empty for successful deletion).
        """
        return self._make_request("DELETE", f"Groups/{group_id}")
    
    def patch_group(self, group_id: str, patch_operations: List[Dict[str, Any]]) -> requests.Response:
        """Apply PATCH operations to a group.
        
        Args:
            group_id: The SCIM group ID.
            patch_operations: List of PATCH operations to apply.
            
        Returns:
            Response object with updated group data.
        """
        patch_data = {
            "schemas": [
                "urn:ietf:params:scim:api:messages:2.0:PatchOp"
            ],
            "Operations": patch_operations
        }
        
        return self._make_request("PATCH", f"Groups/{group_id}", patch_data)
    
    def add_members_to_group(self, group_id: str, user_ids: List[str]) -> requests.Response:
        """Add members to a group using PATCH operation.
        
        Args:
            group_id: The SCIM group ID.
            user_ids: List of user IDs to add to the group.
            
        Returns:
            Response object with updated group data.
        """
        members = [{"value": user_id} for user_id in user_ids]
        operations = [
            {
                "op": "add",
                "path": "members",
                "value": members
            }
        ]
        
        return self.patch_group(group_id, operations)
    
    def remove_members_from_group(self, group_id: str, user_ids: List[str]) -> requests.Response:
        """Remove members from a group using PATCH operation.
        
        Args:
            group_id: The SCIM group ID.
            user_ids: List of user IDs to remove from the group.
            
        Returns:
            Response object with updated group data.
        """
        operations = []
        for user_id in user_ids:
            operations.append({
                "op": "remove",
                "path": f"members[value eq \"{user_id}\"]"
            })
        
        return self.patch_group(group_id, operations)