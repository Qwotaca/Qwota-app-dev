import sqlite3
import requests
import json
import sys
import os

# Forcer l'encodage UTF-8 pour Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("🔍 VÉRIFICATION SYNCHRONISATION MONDAY.COM")
print("=" * 80)
print()

# 1. Vérifier les ventes acceptées dans Qwota
print("📋 VENTES ACCEPTÉES DANS QWOTA:")
print("-" * 80)

ventes_acceptees_path = "data/ventes_acceptees/mathis/ventes.json"

if os.path.exists(ventes_acceptees_path):
    with open(ventes_acceptees_path, "r", encoding="utf-8") as f:
        ventes = json.load(f)

    print(f"✓ Trouvé {len(ventes)} vente(s) acceptée(s)")
    print()

    for idx, vente in enumerate(ventes, 1):
        nom_complet = f"{vente.get('prenom', '')} {vente.get('nom', '')}".strip()
        prix = vente.get('prix', 'N/A')
        telephone = vente.get('telephone', 'N/A')
        adresse = vente.get('adresse', 'N/A')
        email = vente.get('email', vente.get('courriel', 'N/A'))

        print(f"Vente #{idx}:")
        print(f"  • Nom: {nom_complet}")
        print(f"  • Prix: {prix}")
        print(f"  • Téléphone: {telephone}")
        print(f"  • Adresse: {adresse}")
        print(f"  • Email: {email}")
        print()
else:
    print("❌ Aucune vente acceptée trouvée dans Qwota")
    ventes = []

print()
print("=" * 80)

# 2. Récupérer les credentials Monday.com
conn = sqlite3.connect('data/qwota.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT username, monday_api_key, monday_board_id
    FROM users
    WHERE username = 'mathis'
""")

result = cursor.fetchone()
conn.close()

if not result or not result[1] or not result[2]:
    print("❌ Pas de credentials Monday.com configurés pour mathis")
    sys.exit(1)

username, api_key, board_id = result

print("📊 ITEMS DANS MONDAY.COM (Board: FB - Production 2025):")
print("-" * 80)

# 3. Récupérer les items du board Monday.com
url = "https://api.monday.com/v2"
headers = {
    "Authorization": api_key,
    "Content-Type": "application/json"
}

# Query pour récupérer tous les items récents
query = f"""
query {{
  boards(ids: {board_id}) {{
    name
    items_page(limit: 50) {{
      items {{
        id
        name
        created_at
        column_values {{
          id
          text
          value
        }}
      }}
    }}
  }}
}}
"""

response = requests.post(
    url,
    headers=headers,
    json={"query": query}
)

if response.status_code == 200:
    data = response.json()

    if "errors" in data:
        print("❌ Erreur API Monday.com:")
        print(json.dumps(data["errors"], indent=2, ensure_ascii=False))
    elif "data" in data and data["data"]["boards"]:
        board = data["data"]["boards"][0]
        items = board["items_page"]["items"]

        print(f"✓ Trouvé {len(items)} item(s) dans Monday.com")
        print()

        # Récupérer les colonnes du board pour le mapping
        query_columns = f"""
        query {{
          boards(ids: {board_id}) {{
            columns {{
              id
              title
              type
            }}
          }}
        }}
        """

        response_cols = requests.post(url, headers=headers, json={"query": query_columns})
        columns_map = {}

        if response_cols.status_code == 200:
            cols_data = response_cols.json()
            if "data" in cols_data and cols_data["data"]["boards"]:
                for col in cols_data["data"]["boards"][0]["columns"]:
                    columns_map[col["id"]] = col["title"]

        # Afficher les 10 items les plus récents
        items_sorted = sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)

        for idx, item in enumerate(items_sorted[:10], 1):
            print(f"Item #{idx}: {item['name']}")
            print(f"  • ID: {item['id']}")
            print(f"  • Créé le: {item.get('created_at', 'N/A')}")

            # Afficher les valeurs des colonnes importantes
            col_values = {}
            for col_val in item.get('column_values', []):
                if col_val.get('text'):
                    col_name = columns_map.get(col_val['id'], col_val['id'])
                    col_values[col_name] = col_val['text']

            if col_values:
                print("  • Données:")
                if "$JOB" in col_values:
                    print(f"    - Prix: {col_values['$JOB']}")
                if "Téléphone" in col_values:
                    print(f"    - Téléphone: {col_values['Téléphone']}")
                if "Adresse" in col_values:
                    print(f"    - Adresse: {col_values['Adresse']}")
                if "Courriel client" in col_values:
                    print(f"    - Email: {col_values['Courriel client']}")
            print()

        print()
        print("=" * 80)
        print("🔍 ANALYSE:")
        print("-" * 80)

        # Vérifier si les ventes Qwota sont dans Monday.com
        if ventes:
            print(f"Ventes dans Qwota: {len(ventes)}")
            print(f"Items dans Monday.com: {len(items)}")
            print()

            # Chercher les correspondances
            for vente in ventes:
                nom_qwota = f"{vente.get('prenom', '')} {vente.get('nom', '')}".strip()
                trouve = False

                for item in items:
                    if item['name'].lower() == nom_qwota.lower():
                        trouve = True
                        print(f"✓ '{nom_qwota}' trouvé dans Monday.com (ID: {item['id']})")
                        break

                if not trouve:
                    print(f"✗ '{nom_qwota}' PAS TROUVÉ dans Monday.com")

        print()
        print("=" * 80)

    else:
        print("❌ Aucun board trouvé")
else:
    print(f"❌ Erreur HTTP {response.status_code}")
    print(response.text)

print()
print("Vérification terminée!")
print("=" * 80)
