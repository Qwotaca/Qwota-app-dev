import json
import os

# Read coach3's tasks to get Test2
coach3_tasks_path = "data/coach_tasks/coach3_tasks.json"
with open(coach3_tasks_path, 'r', encoding='utf-8') as f:
    coach3_tasks = json.load(f)

# Find Test2 task
test2_task = None
for task in coach3_tasks:
    if task['id'] == '1766265516104':
        test2_task = task
        break

if not test2_task:
    print("Test2 task not found in coach3_tasks.json")
    exit(1)

print(f"Found Test2 task: {test2_task['title']}")
print(f"Assigned users: {test2_task.get('assignedUsers', [])}")

# Read direction's tasks
direction_tasks_path = "data/coach_tasks/direction_tasks.json"
if os.path.exists(direction_tasks_path):
    with open(direction_tasks_path, 'r', encoding='utf-8') as f:
        direction_tasks = json.load(f)
else:
    direction_tasks = []

# Check if Test2 already exists for direction
task_exists = any(t['id'] == test2_task['id'] for t in direction_tasks)

if not task_exists:
    # Add Test2 to direction's tasks
    direction_tasks.append(test2_task)

    # Save to direction_tasks.json
    with open(direction_tasks_path, 'w', encoding='utf-8') as f:
        json.dump(direction_tasks, f, indent=2, ensure_ascii=False)

    print("[OK] Test2 task added to direction_tasks.json")
else:
    print("Test2 task already exists in direction_tasks.json")
