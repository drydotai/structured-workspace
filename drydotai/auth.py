import os
import json
import requests
from typing import Optional, Dict, Any

# Constants
DEFAULT_SERVER = "https://dry.ai"
ENV_SERVER_KEY = "DRY_AI_SERVER"
ENV_TOKEN_KEY = "DRY_AI_TOKEN"
ENV_FILE = ".env"


def _get_server_url() -> str:
    """Get server URL from environment or use default"""
    return os.getenv(ENV_SERVER_KEY, DEFAULT_SERVER)


class _DryAIAuth:
    """
    Authentication wrapper for Dry.ai API
    Handles user registration, login, email verification, and token storage
    """
    
    def __init__(self, server: Optional[str] = None):
        # Use provided server, or environment variable, or default
        if server is None:
            server = _get_server_url()
        self.server = server.rstrip('/')
        self.base_url = f"{self.server}/api/crud-gpt"
        self.token_file = ENV_FILE
        self.current_token = None
        
        # Load existing token from environment
        self._load_token_from_env()
    
    def _load_token_from_env(self) -> None:
        """Load existing token from environment or .env file"""
        # First try environment variable
        token = os.getenv(ENV_TOKEN_KEY)
        if token:
            self.current_token = token
            return
            
        # Then try to load from .env file
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f'{ENV_TOKEN_KEY}='):
                            self.current_token = line.split('=', 1)[1]
                            break
            except Exception:
                pass
    
    def _save_token_to_env(self, token: str) -> None:
        """Save token to .env file"""
        env_lines = []
        token_found = False
        
        # Read existing .env file if it exists
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    env_lines = f.readlines()
            except Exception:
                env_lines = []
        
        # Update or add token line
        new_env_lines = []
        for line in env_lines:
            stripped_line = line.strip()
            # Check if this line contains the token (active or commented)
            if stripped_line.startswith(f'{ENV_TOKEN_KEY}=') or stripped_line.startswith(f'# {ENV_TOKEN_KEY}='):
                new_env_lines.append(f'{ENV_TOKEN_KEY}={token}\n')
                token_found = True
            else:
                # Ensure line ends with newline
                if line and not line.endswith('\n'):
                    line = line + '\n'
                new_env_lines.append(line)
        
        # Add token if not found
        if not token_found:
            new_env_lines.append(f'{ENV_TOKEN_KEY}={token}\n')
        
        # Write back to file
        try:
            with open(self.token_file, 'w') as f:
                f.writelines(new_env_lines)
            
            # Also set in current environment
            os.environ[ENV_TOKEN_KEY] = token
            self.current_token = token
        except Exception as e:
            raise Exception(f"Failed to save token to .env file: {e}")
    
    def register_or_login(self, email: str) -> Dict[str, Any]:
        """
        Register a new user or initiate login for existing user
        Returns registration response with userId
        """
        url = f"{self.base_url}/register-user"
        
        payload = {
            "email": email
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success'):
                print(f"✅ Registration/login initiated for {email}")
                if data.get('isExistingUser'):
                    print("📧 Existing user - verification code sent to email")
                else:
                    print("📧 New user created - verification code sent to email")
                
                return data
            else:
                raise Exception(data.get('message', 'Registration failed'))
                
        except requests.RequestException as e:
            raise Exception(f"Registration request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")
    
    def verify_email(self, code: str, user_id: str, email: str) -> str:
        """
        Verify email with code and return mcpToken
        Automatically stores token in environment
        """
        url = f"{self.base_url}/verify-email"
        
        payload = {
            "code": code,
            "userId": user_id,
            "email": email
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') and data.get('verified'):
                mcp_token = data.get('mcpToken')
                if not mcp_token:
                    raise Exception("No mcpToken returned from verification")
                
                # Store token
                self._save_token_to_env(mcp_token)
                
                print("✅ Email verified successfully!")
                print(f"🔑 Token stored in {self.token_file}")
                
                if data.get('userCreated'):
                    print("👤 New user account created")
                else:
                    print("👤 Logged into existing account")
                
                return mcp_token
            else:
                raise Exception(data.get('message', 'Email verification failed'))
                
        except requests.RequestException as e:
            raise Exception(f"Verification request failed: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}")
    
    def authenticate_user(self, email: str) -> Optional[str]:
        """
        Complete authentication flow: register/login and get verification code from user
        Returns mcpToken if successful
        """
        try:
            # Step 1: Register or login
            print(f"🔐 Starting authentication for {email}...")
            reg_response = self.register_or_login(email)
            
            user_id = reg_response.get('userId')
            if not user_id:
                raise Exception("No userId returned from registration")
            
            # Step 2: Get verification code from user
            print("\n📨 Please check your email for the verification code")
            code = input("Enter verification code: ").strip()
            
            if not code:
                raise Exception("Verification code is required")
            
            # Step 3: Verify email and get token
            token = self.verify_email(code, user_id, email)
            
            return token
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return None
    
    def get_current_token(self) -> Optional[str]:
        """Get currently stored token"""
        return self.current_token
    
    def is_authenticated(self) -> bool:
        """Check if user has a valid token stored"""
        return bool(self.current_token)
    
    def clear_token(self) -> None:
        """Clear stored token from environment and file"""
        self.current_token = None
        
        # Remove from environment
        if ENV_TOKEN_KEY in os.environ:
            del os.environ[ENV_TOKEN_KEY]
        
        # Remove from .env file
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    lines = f.readlines()
                
                new_lines = []
                for line in lines:
                    stripped_line = line.strip()
                    # Keep lines that don't contain the token (active or commented)
                    if not (stripped_line.startswith(f'{ENV_TOKEN_KEY}=') or stripped_line.startswith(f'# {ENV_TOKEN_KEY}=')):
                        new_lines.append(line)
                
                with open(self.token_file, 'w') as f:
                    f.writelines(new_lines)
                    
                print("🔓 Token cleared from environment")
            except Exception as e:
                print(f"Warning: Could not clear token from .env file: {e}")


def authenticate_user(email: str, server: Optional[str] = None) -> Optional[str]:
    """
    Complete authentication flow for a user: register/login and verify email
    Returns mcpToken if successful, automatically stores in .env file
    Uses DRY_AI_SERVER environment variable if no server specified
    """
    auth = _DryAIAuth(server)
    return auth.authenticate_user(email)


def get_stored_token() -> Optional[str]:
    """
    Get currently stored authentication token from environment
    """
    token = os.getenv(ENV_TOKEN_KEY)
    if token:
        return token
        
    # Try to load from .env file
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'{ENV_TOKEN_KEY}='):
                        return line.split('=', 1)[1]
        except Exception:
            pass
    return None


def is_authenticated() -> bool:
    """
    Check if user has a valid token stored
    """
    return bool(get_stored_token())


def clear_stored_token() -> None:
    """
    Clear stored authentication token from environment and .env file
    """
    # Remove from environment
    if ENV_TOKEN_KEY in os.environ:
        del os.environ[ENV_TOKEN_KEY]
    
    # Remove from .env file
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, 'r') as f:
                lines = f.readlines()
            
            new_lines = []
            lines_removed = 0
            for line in lines:
                stripped_line = line.strip()
                # Keep lines that don't contain the token (active or commented)
                if stripped_line.startswith(f'{ENV_TOKEN_KEY}=') or stripped_line.startswith(f'# {ENV_TOKEN_KEY}='):
                    lines_removed += 1
                    # Skip this line (don't add to new_lines)
                else:
                    new_lines.append(line)
            
            with open(ENV_FILE, 'w') as f:
                f.writelines(new_lines)
                
            print(f"🔓 Token cleared from environment ({lines_removed} lines removed)")
        except Exception as e:
            print(f"Warning: Could not clear token from .env file: {e}")