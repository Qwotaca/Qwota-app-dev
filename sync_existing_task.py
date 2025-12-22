import json
import os

# Read the direction task
direction_tasks_path = "data/coach_tasks/direction_tasks.json"
with open(direction_tasks_path, 'r', encoding='utf-8') as f:
    direction_tasks = json.load(f)

# Get the task to sync
task = direction_tasks[0] if direction_tasks else None

if task:
    print(f"Found task: {task['title']}")
    print(f"Assigned users: {task.get('assignedUsers', [])}")

    # Sync to each assigned user
    for user in task.get('assignedUsers', []):
        username = user['username']
        user_tasks_path = f"data/coach_tasks/{username}_tasks.json"

        # Load existing tasks for user
        if os.path.exists(user_tasks_path):
            with open(user_tasks_path, 'r', encoding='utf-8') as f:
                user_tasks = json.load(f)
        else:
            user_tasks = []

        # Check if task already exists
        task_exists = any(t['id'] == task['id'] for t in user_tasks)

        if not task_exists:
            user_tasks.append(task)
            with open(user_tasks_path, 'w', encoding='utf-8') as f:
                json.dump(user_tasks, f, indent=2, ensure_ascii=False)
            print(f"[OK] Added task to {username}")
        else:
            print(f"- Task already exists for {username}")
else:
    print("No task to sync")
