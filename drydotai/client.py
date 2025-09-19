"""
Main client module for dry.ai backend services using CRUD API
"""

import json
import os
import getpass
import requests
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urlencode

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file from current directory
except ImportError:
    # dotenv not installed, continue without it
    pass



class DryAIItem:
    """Wrapper class for items returned from the API"""
    def __init__(self, data: Dict[str, Any], client: 'DryAIClient'):
        self._data = data
        self._client = client
        # Map camelCase API properties to Python lowercase convention
        self.id = data.get('ID')
        self.name = data.get('Name')
        self.description = data.get('Description')
        self.url = data.get('URL')
    
    def update(self, query: str) -> 'DryAIItem':
        """Update this item using natural language instructions"""
        return self._client.update_item(self.id, query)
    
    def delete(self) -> bool:
        """Delete this item"""
        return self._client.delete_item(self.id)
    
    def __getattr__(self, name: str) -> Any:
        """Allow access to all data fields from the API response
        
        Supports both exact key matching and case-insensitive lowercase access.
        For example: item.priority will find "Priority", "priority", or "PRIORITY"
        """
        # First try exact match
        if name in self._data:
            return self._data[name]
        
        # If not found, try case-insensitive matching
        # Look for capitalized version (common API pattern)
        capitalized_name = name.capitalize()
        if capitalized_name in self._data:
            return self._data[capitalized_name]
        
        # Look for uppercase version
        upper_name = name.upper()
        if upper_name in self._data:
            return self._data[upper_name]
        
        # Look for any case-insensitive match
        for key in self._data.keys():
            if key.lower() == name.lower():
                return self._data[key]
        
        # Not found, return None (consistent with dict.get behavior)
        return None
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to item data"""
        return self._data.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style assignment to item data"""
        self._data[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for checking if a key exists"""
        return key in self._data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value with optional default, similar to dict.get()"""
        return self._data.get(key, default)
    
    def keys(self):
        """Return all available keys from the API response"""
        return self._data.keys()
    
    def values(self):
        """Return all values from the API response"""
        return self._data.values()
    
    def items(self):
        """Return all key-value pairs from the API response"""
        return self._data.items()
    
    
    def __repr__(self) -> str:
        return f"DryAIItem(id={self.id}, name={self.name})"


class DryAIClient:
    def __init__(self, auth_token: Optional[str] = None, server_url: Optional[str] = None):
        # Allow server override via parameter or environment variable
        self.server = server_url or os.getenv('DRY_AI_SERVER', 'https://dry.ai')
        # Auto-load auth token from environment if not provided
        self.auth_token = auth_token or os.getenv('DRY_AI_TOKEN')
        self.user_agent = "drydotai-python/1.0"
        
        # CRUD API endpoints
        self.base_url = f"{self.server}/api/crud-gpt"
        self.items_url = f"{self.base_url}/items"
        self.item_url = f"{self.base_url}/item"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests"""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        return headers
    
    def _make_request(self, method: str, url: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request to the API"""
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            print(f"Error making request to {url}: {error}")
            return None
    
    def create_item(self, item_type: str, query: str, folder: Optional[str] = None) -> Optional[DryAIItem]:
        """Create a new item using the CRUD API

        Args:
            item_type: Type of item to create (e.g., 'ITEM', 'FOLDER', 'TYPE')
            query: Natural language description of the item to create
            folder: Optional folder ID to create the item in

        Returns:
            DryAIItem if successful, None otherwise
        """
        data = {
            "type": item_type,
            "query": query,
            "multi": "true"
        }
        if folder:
            data["folder"] = folder
        
        response = self._make_request('POST', self.items_url, data)
        if response and response.get('items'):
            return DryAIItem(response['items'][0], self)
        return None
    
    def get_item(self, item_id: Optional[str] = None, item_type: Optional[str] = None, query: Optional[str] = None) -> Optional[DryAIItem]:
        """Get an item by ID or search for smartspace by query"""
        params = {}
        if item_id:
            params['item'] = item_id
        if item_type:
            params['type'] = item_type
        if query:
            params['query'] = query
        
        response = self._make_request('GET', self.item_url, params=params)
        if response and 'item' in response:
            return DryAIItem(response['item'], self)
        return None
    
    def list_items(self, folder: str, query: str) -> List[DryAIItem]:
        """Search for items in a folder using natural language query

        Args:
            folder: Folder ID to search in
            query: Natural language search query

        Returns:
            List of DryAIItem
        """
        params = {'folder': folder, 'query': query, 'multi': 'true'}
        response = self._make_request('GET', self.items_url, params=params)

        if response and response.get('items'):
            return [DryAIItem(item_data, self) for item_data in response['items']]
        return []
    
    def update_item(self, item_id: str, query: str) -> Optional[DryAIItem]:
        """Update an item using natural language instructions"""
        data = {'item': item_id, 'query': query}
        response = self._make_request('PUT', self.items_url, data)
        
        if response and 'items' in response and response['items']:
            return DryAIItem(response['items'][0], self)
        return None
    
    def update_items(self, folder: str, query: str) -> List[DryAIItem]:
        """Update multiple items in a folder using natural language instructions"""
        data = {'folder': folder, 'query': query}
        response = self._make_request('PUT', self.items_url, data)
        
        if response and 'items' in response:
            return [DryAIItem(item_data, self) for item_data in response['items']]
        return []
    
    def delete_item(self, item_id: str) -> bool:
        """Delete a specific item by ID"""
        params = {'item': item_id}
        response = self._make_request('DELETE', self.items_url, params=params)
        return response is not None
    
    def delete_items_by_query(self, folder: str, query: str) -> bool:
        """Delete items by search query within a folder"""
        params = {'folder': folder, 'query': query}
        response = self._make_request('DELETE', self.items_url, params=params)
        return response is not None


class Smartspace:
    """Main interface for interacting with a Dry.ai smartspace"""
    
    def __init__(self, smartspace_data: DryAIItem, client: DryAIClient):
        self._data = smartspace_data
        self.client = client
        self.id = smartspace_data.id
        self.name = smartspace_data.name
        self.description = smartspace_data.description
        self.url = smartspace_data.url
    
    def search(self, query: str) -> List[DryAIItem]:
        """Search for items in this smartspace using natural language

        Args:
            query: Natural language search query

        Returns:
            List of DryAIItem
        """
        return self.client.list_items(self.id, query)
    
    def add_type(self, query: str) -> Optional[DryAIItem]:
        """Add a new type definition to this smartspace"""
        return self.client.create_item('TYPE', query, self.id)
    
    def add_item(self, query: str) -> Optional[DryAIItem]:
        """Add a new generic item to this smartspace"""
        return self.client.create_item('ITEM', query, self.id)
    
    def add_folder(self, query: str) -> Optional[DryAIItem]:
        """Add a new folder to this smartspace"""
        return self.client.create_item('FOLDER', query, self.id)
    
    def delete_items(self, query: str) -> bool:
        """Delete items in this smartspace that match the query"""
        return self.client.delete_items_by_query(self.id, query)
    
    def update_items(self, query: str) -> List[DryAIItem]:
        """Update multiple items in this smartspace using natural language instructions"""
        return self.client.update_items(self.id, query)
    
    def update(self, query: str) -> 'Smartspace':
        """Update this smartspace using natural language instructions"""
        updated_item = self.client.update_item(self.id, query)
        if updated_item:
            self._data = updated_item
            self.name = updated_item.name
            self.description = updated_item.description
        return self
    
    def delete(self) -> bool:
        """Delete this smartspace"""
        return self.client.delete_item(self.id)
    
    def __repr__(self) -> str:
        return f"Smartspace(id={self.id}, name={self.name})"


def _get_auth_token(auth: Optional[str] = None, auto_authenticate: bool = True) -> Optional[str]:
    """Get auth token from parameter or environment variable, with automatic authentication

    Args:
        auth: Explicitly provided auth token
        auto_authenticate: Whether to automatically prompt for authentication if no token found

    Returns:
        Auth token from parameter, environment variable, or None
    """
    if auth:
        return auth

    # Try environment variable first
    from .auth import get_stored_token
    env_token = get_stored_token()
    if env_token:
        return env_token

    # If no token found and auto_authenticate is True, prompt for authentication
    if auto_authenticate:
        print("🔐 Dry.ai authentication required for first-time setup...")
        print("This will only happen once - your token will be saved for future use.")
        print()

        email = input("Enter your email address: ").strip()
        if not email:
            print("❌ Email is required for authentication")
            return None

        # Import here to avoid circular imports
        from .auth import authenticate_user

        try:
            token = authenticate_user(email)
            if token:
                print("✅ Authentication successful! You're all set.")
                print()
                return token
            else:
                print("❌ Authentication failed. Please try again.")
                return None
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None

    return None




# Global client instance
_client = DryAIClient()


def create_smartspace(query: str, auth: Optional[str] = None) -> Optional[Smartspace]:
    """Create a new smartspace using natural language description
    
    Args:
        query: Natural language description of the smartspace to create
        auth: Auth token (if None, will use DRY_AI_TOKEN environment variable)
        
    Returns:
        Smartspace object if successful, None otherwise
    """
    global _client
    auth_token = _get_auth_token(auth)
    server_url = os.getenv('DRY_AI_SERVER')
    
    # Recreate client if auth or server changed
    if (auth_token and _client.auth_token != auth_token) or (server_url and _client.server != server_url):
        _client = DryAIClient(auth_token=auth_token, server_url=server_url)
    
    item = _client.create_item('SMARTSPACE', query)
    if item:
        return Smartspace(item, _client)
    return None


def get_smartspace(query: str, auth: Optional[str] = None) -> Optional[Smartspace]:
    """Get an existing smartspace by natural language query
    
    Args:
        query: Natural language query to find the smartspace
        auth: Auth token (if None, will use DRY_AI_TOKEN environment variable)
        
    Returns:
        Smartspace object if found, None otherwise
    """
    global _client
    auth_token = _get_auth_token(auth)
    server_url = os.getenv('DRY_AI_SERVER')
    
    # Recreate client if auth or server changed
    if (auth_token and _client.auth_token != auth_token) or (server_url and _client.server != server_url):
        _client = DryAIClient(auth_token=auth_token, server_url=server_url)
    
    item = _client.get_item(item_type='SMARTSPACE', query=query)
    if item:
        return Smartspace(item, _client)
    return None


def get_smartspace_by_id(smartspace_id: str, auth: Optional[str] = None) -> Optional[Smartspace]:
    """Get an existing smartspace by its ID
    
    Args:
        smartspace_id: The unique ID of the smartspace
        auth: Auth token (if None, will use DRY_AI_TOKEN environment variable)
        
    Returns:
        Smartspace object if found, None otherwise
    """
    global _client
    auth_token = _get_auth_token(auth)
    server_url = os.getenv('DRY_AI_SERVER')
    
    # Recreate client if auth or server changed
    if (auth_token and _client.auth_token != auth_token) or (server_url and _client.server != server_url):
        _client = DryAIClient(auth_token=auth_token, server_url=server_url)
    
    item = _client.get_item(item_id=smartspace_id)
    if item:
        return Smartspace(item, _client)
    return None

