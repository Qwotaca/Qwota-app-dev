import sqlite3
import requests
import json

# Get credentials
conn = sqlite3.connect('data/qwota.db')
cursor = conn.cursor()
cursor.execute("SELECT monday_api_key, monday_board_id FROM users WHERE username = 'mathis'")
result = cursor.fetchone()
conn.close()

api_key, board_id = result

url = "https://api.monday.com/v2"
headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}

# Check the latest Joe Dupont item
item_id = "10741762718"

query = f"""
query {{
  items(ids: [{item_id}]) {{
    id
    name
    column_values {{
      id
      type
      text
      value
    }}
  }}
}}
"""

response = requests.post(url, headers=headers, json={"query": query})
data = response.json()

if "data" in data and data["data"]["items"]:
    item = data["data"]["items"][0]
    print(f"Item: {item['name']} (ID: {item['id']})")
    print("-" * 60)

    for col in item["column_values"]:
        if col["text"]:
            print(f"{col['id']:15} ({col['type']:15}) = {col['text']}")
            # Show raw value for $JOB to see the actual number
            if col["id"] == "numbers4":
                print(f"  {'(Raw value)':28} = {col['value']}")
else:
    print("Erreur:", json.dumps(data, indent=2, ensure_ascii=False))
