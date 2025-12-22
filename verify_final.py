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

# Check Marie Tremblay item
item_id = "10741795526"

query = f"""
query {{
  items(ids: [{item_id}]) {{
    id
    name
    column_values {{
      id
      type
      text
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

    columns = {
        "numbers4": "Prix ($JOB)",
        "phone": "Téléphone",
        "location": "Adresse",
        "email": "Courriel client",
        "dup__of_couleurs_mkm0awjt": "Provenance"
    }

    for col in item["column_values"]:
        if col["id"] in columns:
            col_name = columns[col["id"]]
            text = col["text"] if col["text"] else "(vide)"
            status = "OK" if col["text"] else "VIDE"
            print(f"{col_name:20} = {text}")

            if col["id"] == "dup__of_couleurs_mkm0awjt":
                if col["text"] == "PàP":
                    print(f"  {'':18} ✓ Provenance correcte!")
else:
    print("Erreur:", json.dumps(data, indent=2, ensure_ascii=False))
