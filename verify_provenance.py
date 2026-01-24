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

# Check Jean Martin item
item_id = "10741783730"

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
    print("=" * 60)

    for col in item["column_values"]:
        if col["id"] == "dup__of_couleurs_mkm0awjt":
            print(f"\nProvenance (dup__of_couleurs_mkm0awjt):")
            print(f"  Type: {col['type']}")
            print(f"  Text: '{col['text']}'")
            print(f"  Value: {col['value']}")
            if not col['text']:
                print("  ✓ VIDE (succès!)")
            else:
                print(f"  ✗ PAS VIDE: '{col['text']}'")
        elif col["text"]:
            print(f"{col['id']:20} = {col['text']}")
else:
    print("Erreur:", json.dumps(data, indent=2, ensure_ascii=False))
