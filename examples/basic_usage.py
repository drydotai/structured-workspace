"""
Basic Usage Example - Getting started with drydotai
"""

from drydotai import create_smartspace

def main():
    print("🚀 drydotai Basic Usage Example")
    print("=" * 40)

    # 1. Create a workspace (authentication happens automatically if needed)
    print("\n1. Creating a workspace")
    space = create_smartspace("My first project workspace")
    print(f"✅ Created workspace: {space.name}")
    print(f"   Workspace ID: {space.id}")
    print(f"   View at: {space.url}")

    # 2. Add some structure
    print("\n2. Adding structure to workspace")

    # Create a type definition
    task_type = space.add_type("Create a Task type with title, status (todo/in_progress/done), priority (low/medium/high), and due_date fields")
    print("✅ Created Task type")

    # Create a folder
    folder = space.add_folder("Create a folder for completed tasks")
    print("✅ Created folder")

    # 3. Add some content
    print("\n3. Adding content")

    task1 = space.add_item("Create a high priority task: Review code by Friday")
    print(f"✅ Created task: {task1.name}")

    task2 = space.add_item("Create a medium priority task: Update documentation")
    print(f"✅ Created task: {task2.name}")

    task3 = space.add_item("Create a low priority task: Organize team meeting")
    print(f"✅ Created task: {task3.name}")

    # 4. Search for items
    print("\n4. Searching for items")

    high_priority = space.search("find all high priority tasks")
    print(f"Found {len(high_priority)} high priority tasks:")
    for task in high_priority:
        print(f"  - {task.name}")

    all_tasks = space.search("find all tasks")
    print(f"\nFound {len(all_tasks)} total tasks:")
    for task in all_tasks:
        priority = getattr(task, 'priority', 'unknown')
        status = getattr(task, 'status', 'unknown')
        print(f"  - [{status}] {task.name} (Priority: {priority})")

    # 5. Update items
    print("\n5. Updating items")

    if all_tasks:
        first_task = all_tasks[0]
        updated_task = first_task.update("Change status to in_progress and add note: Started working on this")
        print(f"✅ Updated task: {updated_task.name}")
        print(f"   New status: {getattr(updated_task, 'status', 'unknown')}")

    # 6. Bulk operations
    print("\n6. Bulk operations")

    updated_items = space.update_items("update all tasks with status 'todo' to set priority to 'medium'")
    print(f"✅ Bulk updated {len(updated_items)} items")

    # 7. Final search to see results
    print("\n7. Final workspace state")
    final_tasks = space.search("find all tasks")
    print(f"Final workspace has {len(final_tasks)} tasks:")
    for task in final_tasks:
        priority = getattr(task, 'priority', 'unknown')
        status = getattr(task, 'status', 'unknown')
        print(f"  - [{status}] {task.name} (Priority: {priority})")

    print(f"\n🎉 Example complete! View your workspace at: {space.url}")

if __name__ == "__main__":
    main()