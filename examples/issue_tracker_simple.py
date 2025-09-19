"""
Simple Issue Tracker Example
"""

import os
from drydotai import create_smartspace, get_smartspace_by_id

# Configuration
WORKSPACE_NAME = "Issue Tracker"
WORKSPACE_ID_FILE = ".issue_tracker_workspace_id"

def setup_workspace():
    """Set up the issue tracker workspace"""
    print("🔧 Setting up Issue Tracker workspace...")

    # Create workspace (authentication happens automatically if needed)
    space = create_smartspace(WORKSPACE_NAME)

    # Save workspace ID for later use
    with open(WORKSPACE_ID_FILE, 'w') as f:
        f.write(space.id)

    # Create types for issues
    space.add_type("""
    Create an Issue type with fields:
    - title (text)
    - description (text)
    - status (options: open, in_progress, closed)
    - priority (options: low, medium, high, critical)
    - assignee (text)
    """)

    print(f"✅ Setup complete! Workspace: {space.name}")
    print(f"   Workspace ID saved to: {WORKSPACE_ID_FILE}")
    return space

def get_workspace():
    """Get the existing workspace"""
    if not os.path.exists(WORKSPACE_ID_FILE):
        print("Error: No workspace configured. Run setup first.")
        return None

    with open(WORKSPACE_ID_FILE, 'r') as f:
        workspace_id = f.read().strip()

    space = get_smartspace_by_id(workspace_id)
    if not space:
        print("Error: Could not connect to workspace. Run setup again.")
        return None

    return space

def create_issue(title, description="", priority="medium"):
    """Create a new issue"""
    space = get_workspace()
    if not space:
        return None

    issue_desc = f"""
    Create a new issue:
    Title: {title}
    Description: {description}
    Priority: {priority}
    Status: open
    """

    item = space.add_item(issue_desc)
    print(f"✅ Created issue: {title}")
    return item

def list_issues(query=None):
    """List issues"""
    space = get_workspace()
    if not space:
        return []

    search_query = query or "find all issues"
    items = space.search(search_query)

    print(f"Found {len(items)} issues:")
    for item in items:
        status = getattr(item, 'status', 'unknown')
        priority = getattr(item, 'priority', 'unknown')
        print(f"  - [{status}] {item.name} (Priority: {priority})")

    return items

def close_issue(issue_title):
    """Close an issue by title"""
    space = get_workspace()
    if not space:
        return None

    # Find the issue
    issues = space.search(f"find issue with title: {issue_title}")
    if not issues:
        print(f"No issue found with title: {issue_title}")
        return None

    closed_issues = []
    for issue in issues:
        updated = issue.update("Set status to closed")
        closed_issues.append(updated)
        print(f"✅ Closed issue: {issue.name}")

    return closed_issues

def update_issue_priority(issue_title, priority):
    """Update an issue's priority"""
    space = get_workspace()
    if not space:
        return None

    # Find the issue
    issues = space.search(f"find issue with title: {issue_title}")
    if not issues:
        print(f"No issue found with title: {issue_title}")
        return None

    updated_issues = []
    for issue in issues:
        updated = issue.update(f"Set priority to {priority}")
        updated_issues.append(updated)
        print(f"✅ Updated issue priority: {issue.name} -> {priority}")

    return updated_issues

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("""
Issue Tracker Example

Commands:
  python issue_tracker_simple.py setup                      - Set up workspace
  python issue_tracker_simple.py create <title> [desc]      - Create new issue
  python issue_tracker_simple.py list [query]               - List issues
  python issue_tracker_simple.py close <title>              - Close an issue
  python issue_tracker_simple.py priority <title> <level>   - Update priority

Examples:
  python issue_tracker_simple.py setup
  python issue_tracker_simple.py create "Login bug" "Users cannot authenticate"
  python issue_tracker_simple.py list "find open issues"
  python issue_tracker_simple.py close "Login bug"
  python issue_tracker_simple.py priority "Database issue" critical
        """)
        sys.exit(1)

    command = sys.argv[1]

    if command == "setup":
        setup_workspace()
    elif command == "create":
        if len(sys.argv) < 3:
            print("Usage: create <title> [description]")
            sys.exit(1)
        title = sys.argv[2]
        description = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        create_issue(title, description)
    elif command == "list":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        list_issues(query)
    elif command == "close":
        if len(sys.argv) < 3:
            print("Usage: close <title>")
            sys.exit(1)
        title = sys.argv[2]
        close_issue(title)
    elif command == "priority":
        if len(sys.argv) < 4:
            print("Usage: priority <title> <level>")
            sys.exit(1)
        title = sys.argv[2]
        priority = sys.argv[3]
        update_issue_priority(title, priority)
    else:
        print(f"Unknown command: {command}")