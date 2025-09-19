# drydotai

[![PyPI version](https://badge.fury.io/py/drydotai.svg)](https://badge.fury.io/py/drydotai)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight Python SDK for building AI applications with natural language data management. Create, search, and manage structured workspaces using conversational commands.

## Key Features

- **Natural Language Interface** - Interact with data using plain English
- **Auto-Authentication** - Seamless setup with email verification
- **Flexible Data Model** - Dynamic types, folders, and item management
- **Search & Query** - Intelligent content discovery
- **Real-time Updates** - Instant synchronization across applications

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/drydotai/drydotai-agent-python.git
```

> PyPI package coming soon

## Quick Start

```python
from drydotai import create_smartspace

# Create a smartspace - authentication happens automatically
smartspace = create_smartspace("Project Management")

# Add structured data
task_type = smartspace.add_type("""
Create a Task type with:
- title (text)
- status (options: todo, in_progress, done)
- priority (options: low, medium, high)
""")

# Create and manage items
task = smartspace.add_item("Implement user authentication with priority high")
tasks = smartspace.search("find all high priority tasks")

# Update with natural language
task.update("mark as in progress and add note: started implementation")
```

## Core Concepts

### Smartspaces
Intelligent workspaces that organize your data with natural language understanding.

```python
from drydotai import create_smartspace, get_smartspace

# Create new smartspace
smartspace = create_smartspace("Customer support knowledge base")

# Retrieve existing smartspace
smartspace = get_smartspace("find my customer support smartspace")
```

### Dynamic Types
Define structured data models using conversational descriptions.

```python
# Define custom data structures
user_type = smartspace.add_type("""
Create a User type with:
- name (text)
- email (email)
- role (options: admin, user, guest)
- created_at (datetime)
""")

ticket_type = smartspace.add_type("""
Create a SupportTicket type with:
- title (text)
- description (text)
- severity (options: low, medium, high, critical)
- assigned_to (reference to User)
""")
```

### Natural Language Operations

```python
# Create items with context
ticket = smartspace.add_item("""
Create support ticket: Database connection timeout
Severity: critical
Description: Users unable to access application
""")

# Intelligent search
critical_tickets = smartspace.search("find all critical tickets from this week")
unassigned = smartspace.search("show unassigned tickets with high severity")

# Bulk operations
smartspace.update_items("assign all critical tickets to admin users")
smartspace.delete_items("delete all resolved tickets older than 30 days")
```

## Authentication

Authentication is handled automatically on first use. You'll be prompted to enter your email and verification code:

```
🔐 Dry.ai authentication required for first-time setup...
Enter your email address: developer@company.com
📧 Verification code sent to email
Enter verification code: 123456
✅ Authentication successful!
```
### Core Functions

| Function | Description |
|----------|-------------|
| `create_smartspace(description)` | Create new smartspace with natural language |
| `get_smartspace(query)` | Find existing smartspace by description |
| `get_smartspace_by_id(id)` | Retrieve smartspace by ID |

### Smartspace Methods

| Method | Description |
|--------|-------------|
| `add_type(description)` | Define structured data type |
| `add_item(description)` | Create new item |
| `add_folder(description)` | Create organizational folder |
| `search(query)` | Find items using natural language |
| `update_items(query)` | Bulk update multiple items |
| `delete_items(query)` | Delete items matching query |
| `update(query)` | Update smartspace properties |
| `delete()` | Delete entire smartspace |

### Item Operations

```python
# Individual item management
item.update("change priority to high and assign to john@company.com")
item.delete()

# Access structured data
print(f"Task: {item.title}")
print(f"Status: {item.status}")
print(f"Priority: {item.priority}")
```

## Use Cases

### Project Management
```python
project = create_smartspace("Software development project tracker")

# Define project structure
project.add_type("Epic with title, description, and story points")
project.add_type("User story linked to Epic with acceptance criteria")
project.add_type("Task linked to User story with time estimates")

# Create and track work
epic = project.add_item("User authentication epic with 13 story points")
stories = project.search("find all user stories for authentication epic")
```

### Knowledge Management
```python
kb = create_smartspace("Technical documentation system")

# Structure knowledge
kb.add_type("Article with title, content, tags, and last_updated")
kb.add_type("FAQ with question, answer, and category")

# Content management
article = kb.add_item("API integration guide with authentication patterns")
faqs = kb.search("find all authentication related FAQs")
```

### Data Integration
```python
# Process external data
for user_data in external_api.get_users():
    smartspace.add_item(f"""
    Create user: {user_data['name']}
    Email: {user_data['email']}
    Role: {user_data['role']}
    """)

# Query and analyze
active_users = smartspace.search("find all users who logged in this month")
```

## Examples

Complete working examples available in [`examples/`](examples/):

- **[`demo.ipynb`](examples/demo.ipynb)** - Interactive Jupyter notebook walkthrough
- **[`basic_usage.py`](examples/basic_usage.py)** - Core functionality demonstration
- **[`issue_tracker_simple.py`](examples/issue_tracker_simple.py)** - Issue tracking system

```bash
# Run examples
python examples/basic_usage.py
python examples/issue_tracker_simple.py setup
jupyter notebook examples/demo.ipynb
```

## Requirements

- **Python 3.8+**
- **requests >= 2.25.0**

### Optional Dependencies
- `python-dotenv >= 0.19.0` - Environment file support
- `jupyter` - Interactive notebooks

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [GitHub README](https://github.com/drydotai/drydotai-agent-python)
- **Issues**: [GitHub Issues](https://github.com/drydotai/drydotai-agent-python/issues)
- **Homepage**: [https://dry.ai](https://dry.ai)