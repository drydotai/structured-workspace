# drydotai

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

```bash
pip install git+https://github.com/drydotai/structured-workspace.git@alpha
```

## Quick Start

```python
from drydotai import create_space, set_verbose_logging

# Enable verbose logging to see when API calls complete successfully
set_verbose_logging(True)

# Create a space - authentication happens automatically
space = create_space("Project Management")

# Add structured data
task_type = space.add_type("Create a Task type with title, status (todo/in_progress/done), and priority (low/medium/high)")

# Create and manage items
task = space.add_item("Implement user authentication with priority high")
tasks = space.search("find all high priority tasks")

# Update with natural language
task.update("mark as in progress and add note: started implementation")

# Share workspace with team members
space.update("Share member access with user1@example.com, teammate@example.com, and demo@example.com")

# Set a custom subdomain for the workspace
space.update("Set subdomain to firstprojectspace")
```

## Core Concepts

### Spaces
Intelligent workspaces that organize your data with natural language understanding.

```python
from drydotai import create_space, get_space

# Create new space
space = create_space("Customer support knowledge base")

# Retrieve existing space
space = get_space("find my customer support space")
```

### Dynamic Types
Define structured data models using conversational descriptions.

```python
# Define custom data structures
user_type = space.add_type("""
Create a User type with:
- name (text)
- email (email)
- role (options: admin, user, guest)
- created_at (datetime)
""")

ticket_type = space.add_type("""
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
ticket = space.add_item("""
Create support ticket: Database connection timeout
Severity: critical
Description: Users unable to access application
""")

# Intelligent search
critical_tickets = space.search("find all critical tickets from this week")
unassigned = space.search("show unassigned tickets with high severity")

# Bulk operations
space.update_items("assign all critical tickets to admin users")
space.delete_items("delete all resolved tickets older than 30 days")
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
| `create_space(description)` | Create new space with natural language |
| `get_space(query)` | Find existing space by description |
| `get_space_by_id(id)` | Retrieve space by ID |

### Space Methods

| Method | Description |
|--------|-------------|
| `add_type(description)` | Define structured data type |
| `add_item(description)` | Create new item |
| `add_folder(description)` | Create organizational folder |
| `search(query)` | Find items using natural language |
| `update_items(query)` | Bulk update multiple items |
| `delete_items(query)` | Delete items matching query |
| `update(query)` | Update space properties |
| `delete()` | Delete entire space |

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
project = create_space("Software development project tracker")

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
kb = create_space("Technical documentation system")

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
    space.add_item(f"""
    Create user: {user_data['name']}
    Email: {user_data['email']}
    Role: {user_data['role']}
    """)

# Query and analyze
active_users = space.search("find all users who logged in this month")
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

- **Documentation**: [GitHub README](https://github.com/drydotai/structured-workspace)
- **Issues**: [GitHub Issues](https://github.com/drydotai/structured-workspace/issues)
- **Homepage**: [https://dry.ai](https://dry.ai)