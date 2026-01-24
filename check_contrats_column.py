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

# Récupérer les colonnes du board
query = f'''
query {{
  boards(ids: [{board_id}]) {{
    columns {{
      id
      title
      type
      settings_str
    }}
  }}
}}
'''

response = requests.post(url, headers=headers, json={"query": query})
data = response.json()

if "data" in data and data["data"]["boards"]:
    columns = data["data"]["boards"][0]["columns"]

    print("Colonnes de type 'file':")
    print("=" * 60)

    for col in columns:
        if col['type'] == 'file':
            print(f"\nColonne: {col['title']}")
            print(f"  ID: {col['id']}")
            print(f"  Type: {col['type']}")
            print(f"  Settings: {col['settings_str']}")
