"""
drydotai - Python client library for dry.ai backend services using CRUD API
"""

from .client import (
    Space,
    DryAIItem,
    create_space,
    get_space,
    get_space_by_id,
    set_verbose_logging
)

from .auth import (
    authenticate_user,
    get_stored_token,
    is_authenticated,
    clear_stored_token
)

__version__ = "0.2.0"
__all__ = [
    "Space",
    "DryAIItem",
    "create_space",
    "get_space",
    "get_space_by_id",
    "set_verbose_logging",
    "authenticate_user",
    "get_stored_token",
    "is_authenticated",
    "clear_stored_token"
]