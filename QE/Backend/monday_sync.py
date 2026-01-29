"""
Module de synchronisation avec Monday.com
Gère la création automatique d'items dans Monday.com quand une vente est acceptée
"""

import requests
import sqlite3
from typing import Optional, Dict, Set
import os
import sys
import json
from datetime import datetime
import urllib.parse

# Configuration des chemins selon l'environnement
if sys.platform == 'win32':
    # Windows - développement local
    base_cloud = "data"
else:
    # Unix/Linux (Production sur Render)
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")

DB_PATH = os.path.join(base_cloud, "qwota.db")


def get_closest_monday_color(qwota_color: str) -> int:
    """
    Trouve la couleur Monday la plus proche d'une couleur hexadécimale

    Args:
        qwota_color: Couleur hex (ex: "#ff8c42")

    Returns:
        int: ID de la couleur Monday (0-40)
    """
    # Mapping des couleurs Monday (palette standard)
    monday_colors = {
        0: "#00c875",   # Vert
        1: "#9cd326",   # Vert clair
        2: "#cab641",   # Jaune-vert
        3: "#ffcb00",   # Jaune
        4: "#fdab3d",   # Orange clair
        5: "#ff642e",   # Orange
        6: "#ff158a",   # Rose
        7: "#e2445c",   # Rouge
        8: "#bb3354",   # Rouge foncé
        9: "#a25ddc",   # Violet
        10: "#784bd1",  # Violet foncé
        11: "#0086c0",  # Bleu
        12: "#579bfc",  # Bleu clair
        13: "#66ccff",  # Cyan
        14: "#68a1bd",  # Bleu-gris
        15: "#9aadbd",  # Gris-bleu
        16: "#c4c4c4",  # Gris
        17: "#808080",  # Gris foncé
        18: "#333333",  # Noir
    }

    # Convertir couleur hex en RGB
    qwota_rgb = tuple(int(qwota_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

    # Trouver la couleur Monday la plus proche
    min_distance = float('inf')
    closest_id = 0

    for color_id, hex_color in monday_colors.items():
        monday_rgb = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        # Distance euclidienne
        distance = sum((qwota_rgb[i] - monday_rgb[i]) ** 2 for i in range(3)) ** 0.5

        if distance < min_distance:
            min_distance = distance
            closest_id = color_id

    return closest_id


def add_label_to_monday_column(api_key: str, board_id: str, column_id: str, label_name: str, color: str = "#3b82f6") -> Optional[int]:
    """
    Ajoute une nouvelle étiquette à une colonne Monday via l'API REST

    Args:
        api_key: Clé API Monday.com
        board_id: ID du board Monday.com
        column_id: ID de la colonne
        label_name: Nom de l'étiquette à ajouter
        color: Couleur hex de l'étiquette Qwota

    Returns:
        Optional[int]: Index de la nouvelle étiquette créée, None si échec
    """
    try:
        # Utiliser l'API GraphQL pour récupérer les settings actuels
        url = "https://api.monday.com/v2"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
            "API-Version": "2024-01"
        }

        # 1. Récupérer les settings actuels
        query = f"""
        query {{
          boards(ids: {board_id}) {{
            columns(ids: ["{column_id}"]) {{
              id
              settings_str
            }}
          }}
        }}
        """

        response = requests.post(url, headers=headers, json={"query": query})
        if response.status_code != 200:
            print(f"[MONDAY ERROR] Erreur récupération settings: {response.status_code}")
            return None

        data = response.json()
        if "data" not in data or not data["data"]["boards"]:
            print(f"[MONDAY ERROR] Board non trouvé")
            return None

        columns = data["data"]["boards"][0]["columns"]
        if not columns:
            print(f"[MONDAY ERROR] Colonne non trouvée")
            return None

        settings = json.loads(columns[0]["settings_str"])
        labels = settings.get("labels", {})
        labels_ids_style = settings.get("labels_ids_style", {})
        labels_colors = settings.get("labels_colors", {})

        # 2. Trouver le prochain index disponible
        existing_indices = [int(idx) for idx in labels.keys() if idx.isdigit()]
        new_index = max(existing_indices) + 1 if existing_indices else 0

        # Vérifier si le label existe déjà
        for idx, existing_label in labels.items():
            if existing_label == label_name:
                print(f"[MONDAY] Label '{label_name}' existe déjà (index {idx})")
                return int(idx)

        # 3. Ajouter la nouvelle étiquette
        labels[str(new_index)] = label_name

        # Trouver la couleur Monday la plus proche
        color_id = get_closest_monday_color(color)
        labels_colors[str(new_index)] = {"color": color_id, "border": color_id}

        # Style par défaut
        labels_ids_style[str(new_index)] = 1

        # 4. Mettre à jour les settings
        settings["labels"] = labels
        settings["labels_colors"] = labels_colors
        settings["labels_ids_style"] = labels_ids_style

        # Essayer avec l'API REST Monday
        rest_url = f"https://api.monday.com/v2/boards/{board_id}/columns/{column_id}.json"

        payload = {
            "settings_str": json.dumps(settings)
        }

        rest_response = requests.put(rest_url, headers=headers, json=payload)

        if rest_response.status_code == 200:
            print(f"[MONDAY] ✓ Étiquette '{label_name}' créée avec succès via REST API (index {new_index})")
            return new_index
        else:
            print(f"[MONDAY ERROR] Erreur REST API: {rest_response.status_code}")
            print(f"[MONDAY ERROR] Response: {rest_response.text}")

            # Fallback : essayer avec GraphQL change_column_value
            # Créer directement un item avec cette valeur pour forcer la création du label
            print(f"[MONDAY] Tentative méthode alternative...")
            return None

    except Exception as e:
        print(f"[MONDAY ERROR] Exception création étiquette: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_monday_column_labels(api_key: str, board_id: str, column_id: str) -> Dict[str, int]:
    """
    Récupère les labels d'une colonne Monday et retourne un mapping nom->index

    Args:
        api_key: Clé API Monday.com
        board_id: ID du board Monday.com
        column_id: ID de la colonne

    Returns:
        Dict[str, int]: Mapping nom d'étiquette -> index Monday
    """
    try:
        url = "https://api.monday.com/v2"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        query = f"""
        query {{
          boards(ids: {board_id}) {{
            columns(ids: ["{column_id}"]) {{
              id
              settings_str
            }}
          }}
        }}
        """

        response = requests.post(url, headers=headers, json={"query": query})

        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]["boards"]:
                columns = data["data"]["boards"][0]["columns"]
                if columns:
                    settings = json.loads(columns[0]["settings_str"])
                    labels = settings.get("labels", {})

                    # Créer le mapping nom -> index
                    label_map = {}
                    for idx, label_name in labels.items():
                        # Normaliser le nom pour comparaison (minuscules, sans accents)
                        label_normalized = label_name.strip().lower()
                        label_map[label_normalized] = int(idx)
                        # Aussi garder le nom original
                        label_map[label_name.strip()] = int(idx)

                    return label_map

        return {}
    except Exception as e:
        print(f"[MONDAY ERROR] Erreur récupération labels: {e}")
        return {}


def get_monday_credentials(username: str) -> tuple[Optional[str], Optional[str]]:
    """
    Récupère les credentials Monday.com d'un utilisateur depuis la base de données

    Args:
        username: Username de l'entrepreneur

    Returns:
        tuple: (api_key, board_id) ou (None, None) si non configuré
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT monday_api_key, monday_board_id
                FROM users
                WHERE username = ?
            """, (username,))

            result = cursor.fetchone()

            if result and result[0] and result[1]:
                return result[0], result[1]
            else:
                print(f"[MONDAY] Pas de credentials Monday.com configurés pour {username}")
                return None, None

    except Exception as e:
        print(f"[MONDAY ERROR] Erreur récupération credentials: {e}")
        return None, None


def get_monday_ban_file(username: str) -> str:
    """
    Retourne le chemin du fichier de ban Monday pour un entrepreneur

    Args:
        username: Username de l'entrepreneur

    Returns:
        str: Chemin vers monday_ban.json
    """
    user_dir = os.path.join(base_cloud, "monday_bans", username)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "monday_ban.json")


def load_monday_bans(username: str) -> Set[str]:
    """
    Charge la liste des IDs bannis (déjà envoyés à Monday)

    Args:
        username: Username de l'entrepreneur

    Returns:
        Set[str]: Ensemble des IDs bannis
    """
    ban_file = get_monday_ban_file(username)

    if not os.path.exists(ban_file):
        return set()

    try:
        with open(ban_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('banned_ids', []))
    except Exception as e:
        print(f"[MONDAY BAN] Erreur lecture fichier ban: {e}")
        return set()


def add_to_monday_ban(username: str, item_id: str) -> bool:
    """
    Ajoute un ID à la liste des bannis (pour ne plus jamais l'envoyer à Monday)

    Args:
        username: Username de l'entrepreneur
        item_id: ID de la soumission/vente à bannir

    Returns:
        bool: True si succès, False sinon
    """
    try:
        ban_file = get_monday_ban_file(username)

        # Charger les bans existants
        banned_ids = load_monday_bans(username)

        # Ajouter le nouvel ID
        banned_ids.add(str(item_id))

        # Sauvegarder
        data = {
            'banned_ids': list(banned_ids),
            'last_updated': datetime.now().isoformat()
        }

        with open(ban_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[MONDAY BAN] ID {item_id} ajouté à la liste des bannis pour {username}")
        return True

    except Exception as e:
        print(f"[MONDAY BAN] Erreur ajout ban: {e}")
        return False


def is_banned_from_monday(username: str, item_id: str) -> bool:
    """
    Vérifie si un ID est banni (déjà envoyé à Monday)

    Args:
        username: Username de l'entrepreneur
        item_id: ID de la soumission/vente à vérifier

    Returns:
        bool: True si banni, False sinon
    """
    banned_ids = load_monday_bans(username)
    return str(item_id) in banned_ids


def find_existing_monday_item(api_key: str, board_id: str, soumission_num: str, prenom: str = None, nom: str = None) -> Optional[str]:
    """
    Recherche un item existant dans Monday.com par numéro de soumission

    Args:
        api_key: Clé API Monday.com
        board_id: ID du board Monday.com
        soumission_num: Numéro de soumission à rechercher

    Returns:
        Optional[str]: ID de l'item si trouvé, None sinon
    """
    try:
        url = "https://api.monday.com/v2"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        # Query pour rechercher tous les items du board
        query = f"""
        query {{
          boards(ids: {board_id}) {{
            items_page(limit: 500) {{
              items {{
                id
                name
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

        response = requests.post(url, headers=headers, json={"query": query})

        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"]["boards"]:
                items = data["data"]["boards"][0]["items_page"]["items"]

                # Construire le nom complet pour la recherche par nom
                nom_complet_recherche = None
                if prenom and nom:
                    nom_complet_recherche = f"{prenom} {nom}".strip().lower()
                    print(f"[MONDAY DEBUG] Recherche par nom: '{nom_complet_recherche}'")

                print(f"[MONDAY DEBUG] {len(items)} items à examiner")

                # Chercher un item qui correspond
                for item in items:
                    item_name = item.get("name", "")
                    item_name_lower = item_name.lower()
                    print(f"[MONDAY DEBUG] Examen item: '{item_name}'")

                    # Méthode 1: Vérifier si le numéro de soumission est dans le nom (nouveau format)
                    if soumission_num and soumission_num in item_name:
                        print(f"[MONDAY] Item existant trouvé par numéro dans nom: {item_name} (ID: {item['id']})")
                        return item["id"]

                    # Méthode 2: Vérifier si le nom complet correspond exactement (ancien format)
                    if nom_complet_recherche and nom_complet_recherche in item_name_lower:
                        print(f"[MONDAY] Item existant trouvé par nom complet: {item_name} (ID: {item['id']})")
                        return item["id"]

                    # Méthode 3: Vérifier dans la colonne $JOB (au cas où le numéro y serait)
                    for col_value in item.get("column_values", []):
                        if col_value.get("id") == "numbers4":  # Colonne $JOB
                            job_num = col_value.get("text", "")
                            if job_num and soumission_num in job_num:
                                print(f"[MONDAY] Item existant trouvé par $JOB: {item_name} (ID: {item['id']}, Job: {job_num})")
                                return item["id"]

                print(f"[MONDAY] Aucun item existant trouvé avec le numéro {soumission_num}")
                return None
            else:
                print(f"[MONDAY] Aucun item trouvé dans le board")
                return None
        else:
            print(f"[MONDAY WARN] Erreur recherche items: HTTP {response.status_code}")
            return None

    except Exception as e:
        print(f"[MONDAY WARN] Erreur lors de la recherche: {e}")
        return None


def create_monday_item(api_key: str, board_id: str, item_data: Dict, username: str) -> bool:
    """
    Crée un nouvel item dans Monday.com (seulement si pas banni et pas de doublon)

    Args:
        api_key: Clé API Monday.com
        board_id: ID du board Monday.com
        item_data: Dictionnaire contenant les données du client
        username: Username de l'entrepreneur (pour le système de ban)

    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Extraire les données du client
        prenom = item_data.get('prenom') or item_data.get('clientPrenom', '')
        nom = item_data.get('nom') or item_data.get('clientNom', '')
        nom_complet = f"{prenom} {nom}".strip()
        prix = item_data.get('prix', '')
        depot = item_data.get('depot', '')
        telephone = item_data.get('telephone', '')
        adresse = item_data.get('adresse', '')
        courriel = item_data.get('email', item_data.get('courriel', ''))
        soumission_num = item_data.get('num') or item_data.get('id', '')

        # VÉRIFICATION #1: Vérifier si l'ID est BANNI (déjà envoyé localement)
        if is_banned_from_monday(username, soumission_num):
            print(f"[MONDAY BAN] ⛔ ID {soumission_num} est BANNI - Ne sera JAMAIS envoyé à Monday")
            print(f"[MONDAY BAN] Ce client a déjà été synchronisé précédemment")
            return True  # Retourner True car ce n'est pas une erreur, juste un ban

        print(f"[MONDAY] Vérification doublon pour soumission #{soumission_num}: {nom_complet}")

        # VÉRIFICATION #2: Vérifier si un item existe déjà dans Monday.com
        existing_item_id = find_existing_monday_item(api_key, board_id, str(soumission_num), prenom, nom)
        if existing_item_id:
            print(f"[MONDAY] ⚠️ DOUBLON DÉTECTÉ dans Monday! L'item existe déjà (ID: {existing_item_id})")
            print(f"[MONDAY] ✓ Création ignorée pour éviter le doublon")
            # BANNIR cet ID pour ne plus jamais essayer de l'envoyer
            add_to_monday_ban(username, soumission_num)
            return True  # Retourner True car ce n'est pas une erreur, juste un doublon évité

        print(f"[MONDAY] Création item pour: {nom_complet}")
        print(f"[MONDAY] Prix: {prix}, Tel: {telephone}, Courriel: {courriel}")

        # URL de l'API Monday.com
        url = "https://api.monday.com/v2"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        # Préparer les valeurs des colonnes
        column_values = {}

        # $JOB - Prix (colonne de type numbers)
        if prix:
            try:
                # Nettoyer le prix (enlever espaces, $, etc.)
                prix_str = str(prix).replace('$', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
                # Remplacer virgule par point pour les décimales
                prix_str = prix_str.replace(',', '.')
                prix_num = float(prix_str)
                column_values["numbers4"] = str(prix_num)
            except Exception as e:
                print(f"[MONDAY WARN] Impossible de parser le prix: {prix} - {e}")

        # $ DÉPÔT - Dépôt (colonne de type numbers)
        if depot:
            try:
                # Nettoyer le dépôt (enlever espaces, $, etc.)
                depot_str = str(depot).replace('$', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
                # Remplacer virgule par point pour les décimales
                depot_str = depot_str.replace(',', '.')
                depot_num = float(depot_str)
                column_values["numbers1"] = str(depot_num)
                print(f"[MONDAY] Dépôt ajouté: {depot_num}$")
            except Exception as e:
                print(f"[MONDAY WARN] Impossible de parser le dépôt: {depot} - {e}")

        # Pour Monday.com, les colonnes phone, location et email nécessitent un format JSON spécifique
        # On va les envoyer séparément avec change_column_value après la création

        # Convertir column_values en JSON string pour GraphQL
        import json
        column_values_json = json.dumps(column_values).replace('"', '\\"')

        # Nom de l'item = seulement prénom + nom (pas de numéro visible)
        item_name = nom_complet

        # Query GraphQL pour créer l'item
        query = f"""
        mutation {{
          create_item (
            board_id: {board_id},
            item_name: "{item_name}",
            column_values: "{column_values_json}"
          ) {{
            id
            name
          }}
        }}
        """

        print(f"[MONDAY] Envoi requête à Monday.com...")

        # Envoyer la requête
        response = requests.post(
            url,
            headers=headers,
            json={"query": query}
        )

        if response.status_code == 200:
            data = response.json()

            if "errors" in data:
                print(f"[MONDAY ERROR] Erreur API Monday.com:")
                print(json.dumps(data["errors"], indent=2))
                return False
            elif "data" in data and data["data"]["create_item"]:
                item_id = data["data"]["create_item"]["id"]
                item_name = data["data"]["create_item"]["name"]
                print(f"[MONDAY SUCCESS] Item cree dans Monday.com!")
                print(f"[MONDAY] ID: {item_id}, Nom: {item_name}")

                # Maintenant mettre à jour les colonnes phone, location et email
                # Ces colonnes nécessitent un format spécial avec change_column_value
                if telephone:
                    # Enlever les tirets et ajouter 1 au début si nécessaire
                    tel_clean = str(telephone).strip().replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
                    if not tel_clean.startswith('1') and len(tel_clean) == 10:
                        tel_clean = '1' + tel_clean

                    tel_value_json = json.dumps({"phone": tel_clean, "countryShortName": "CA"})
                    tel_escaped = tel_value_json.replace('"', '\\"')
                    query_tel = f'mutation {{ change_column_value(board_id: {board_id}, item_id: {item_id}, column_id: "phone", value: "{tel_escaped}") {{ id }} }}'

                    resp_tel = requests.post(url, headers=headers, json={"query": query_tel})
                    if resp_tel.status_code == 200 and "errors" not in resp_tel.json():
                        print(f"[MONDAY] Telephone mis a jour")
                    else:
                        print(f"[MONDAY WARN] Erreur mise a jour telephone: {resp_tel.text}")

                if adresse:
                    # Format simple: "lat lng address" - on utilise 0 0 comme coordonnées
                    # Monday.com affichera le texte de l'adresse
                    addr_value = f"0 0 {str(adresse).strip()}"
                    query_addr = f'mutation {{ change_simple_column_value(board_id: {board_id}, item_id: {item_id}, column_id: "location", value: "{addr_value}") {{ id }} }}'

                    resp_addr = requests.post(url, headers=headers, json={"query": query_addr})
                    if resp_addr.status_code == 200 and "errors" not in resp_addr.json():
                        print(f"[MONDAY] Adresse mise a jour")
                    else:
                        print(f"[MONDAY WARN] Erreur mise a jour adresse: {resp_addr.text}")

                if courriel:
                    email_value_json = json.dumps({"email": str(courriel).strip(), "text": str(courriel).strip()})
                    email_escaped = email_value_json.replace('"', '\\"')
                    query_email = f'mutation {{ change_column_value(board_id: {board_id}, item_id: {item_id}, column_id: "email", value: "{email_escaped}") {{ id }} }}'

                    resp_email = requests.post(url, headers=headers, json={"query": query_email})
                    if resp_email.status_code == 200 and "errors" not in resp_email.json():
                        print(f"[MONDAY] Email mis a jour")
                    else:
                        print(f"[MONDAY WARN] Erreur mise a jour email: {resp_email.text}")

                # Mettre la colonne Provenance à "PàP" (index 0)
                provenance_value = json.dumps({"index": 0})
                provenance_escaped = provenance_value.replace('"', '\\"')
                query_provenance = f'mutation {{ change_column_value(board_id: {board_id}, item_id: {item_id}, column_id: "dup__of_couleurs_mkm0awjt", value: "{provenance_escaped}") {{ id }} }}'
                resp_prov = requests.post(url, headers=headers, json={"query": query_provenance})
                if resp_prov.status_code == 200 and "errors" not in resp_prov.json():
                    print(f"[MONDAY] Provenance mise a jour (PaP)")
                else:
                    print(f"[MONDAY WARN] Erreur mise a jour Provenance: {resp_prov.text}")

                # Ajouter les notes dans la colonne "Infos sup" (ID: "text")
                notes = item_data.get('notes', '')
                if notes:
                    # Échapper les caractères spéciaux pour GraphQL
                    notes_escaped = notes.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                    query_notes = f'mutation {{ change_simple_column_value(board_id: {board_id}, item_id: {item_id}, column_id: "text", value: "{notes_escaped}") {{ id }} }}'
                    resp_notes = requests.post(url, headers=headers, json={"query": query_notes})
                    if resp_notes.status_code == 200 and "errors" not in resp_notes.json():
                        print(f"[MONDAY] Notes ajoutées")
                    else:
                        print(f"[MONDAY WARN] Erreur ajout notes: {resp_notes.text}")

                # Ajouter le PDF de la soumission signée dans la colonne Contrats
                pdf_url = item_data.get('pdfUrl') or item_data.get('pdf_url')
                if pdf_url:
                    # Convertir l'URL en chemin de fichier local (localhost ou production)
                    # Toutes les URLs internes contiennent /cloud/ dans le chemin
                    if '/cloud/' in pdf_url:
                        # Extraire le chemin du fichier depuis l'URL
                        pdf_path = pdf_url.split('/cloud/')[-1]
                        pdf_full_path = os.path.join(base_cloud, pdf_path.replace('/', os.sep))
                        print(f"[MONDAY] Chemin PDF: {pdf_full_path}")

                        if os.path.exists(pdf_full_path):
                            try:
                                # Lire le fichier PDF
                                with open(pdf_full_path, 'rb') as pdf_file:
                                    # GraphQL mutation pour ajouter le fichier
                                    query_file = f'mutation($file: File!) {{ add_file_to_column(file: $file, item_id: {item_id}, column_id: "dup__of_gqp") {{ id }} }}'

                                    # Monday.com file upload via https://api.monday.com/v2/file
                                    file_response = requests.post(
                                        'https://api.monday.com/v2/file',
                                        headers={"Authorization": api_key},
                                        data={'query': query_file},
                                        files={'variables[file]': (os.path.basename(pdf_full_path), pdf_file, 'application/pdf')}
                                    )

                                    if file_response.status_code == 200:
                                        resp_data = file_response.json()
                                        if "errors" not in resp_data:
                                            print(f"[MONDAY] PDF contrat ajoute")
                                        else:
                                            print(f"[MONDAY WARN] Erreur ajout PDF: {json.dumps(resp_data['errors'])}")
                                    else:
                                        print(f"[MONDAY WARN] Erreur HTTP ajout PDF: {file_response.status_code} - {file_response.text}")
                            except Exception as e:
                                print(f"[MONDAY WARN] Erreur lecture PDF: {e}")
                        else:
                            print(f"[MONDAY WARN] PDF introuvable: {pdf_full_path}")
                    else:
                        # URL publique externe - essayer de l'ajouter directement
                        print(f"[MONDAY INFO] URL PDF externe (non supportée): {pdf_url}")
                else:
                    print(f"[MONDAY INFO] Aucun PDF dans les donnees de vente")

                # BANNIR cet ID pour ne JAMAIS le renvoyer à Monday
                add_to_monday_ban(username, soumission_num)
                print(f"[MONDAY BAN] ✓ ID {soumission_num} ajouté à la liste des bannis - Ne sera plus jamais envoyé")

                return True
            else:
                print(f"[MONDAY ERROR] Reponse inattendue de Monday.com:")
                print(json.dumps(data, indent=2))
                return False
        else:
            print(f"[MONDAY ERROR] HTTP {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"[MONDAY ERROR] Exception lors de la création: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_monday_column(api_key: str, board_id: str, item_id: str, column_id: str, value: str) -> bool:
    """
    Met à jour une colonne dans un item Monday existant

    Args:
        api_key: Clé API Monday.com
        board_id: ID du board Monday.com
        item_id: ID de l'item à mettre à jour
        column_id: ID de la colonne à mettre à jour
        value: Nouvelle valeur (pour les colonnes dropdown, utiliser l'index)

    Returns:
        bool: True si succès, False sinon
    """
    try:
        url = "https://api.monday.com/v2"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        # Pour les colonnes dropdown (provenance, type), la valeur doit être {"index": X}
        import json
        value_escaped = value.replace('"', '\\"')

        query = f'mutation {{ change_column_value(board_id: {board_id}, item_id: {item_id}, column_id: "{column_id}", value: "{value_escaped}") {{ id }} }}'

        response = requests.post(url, headers=headers, json={"query": query})

        if response.status_code == 200:
            resp_data = response.json()
            if "errors" not in resp_data:
                print(f"[MONDAY] Colonne {column_id} mise à jour avec succès")
                return True
            else:
                print(f"[MONDAY ERROR] Erreur mise à jour colonne: {resp_data['errors']}")
                return False
        else:
            print(f"[MONDAY ERROR] HTTP {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"[MONDAY ERROR] Exception mise à jour colonne: {e}")
        return False


def update_monday_text_column(api_key: str, board_id: str, item_id: str, column_id: str, value: str) -> bool:
    """
    Met à jour une colonne de type TEXT dans Monday.com

    Args:
        api_key: Clé API Monday.com
        board_id: ID du board Monday.com
        item_id: ID de l'item à mettre à jour
        column_id: ID de la colonne texte à mettre à jour
        value: Nouveau texte

    Returns:
        bool: True si succès, False sinon
    """
    try:
        url = "https://api.monday.com/v2"
        headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }

        # Pour les colonnes texte, la valeur doit être une simple chaîne
        import json
        value_escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

        query = f'mutation {{ change_simple_column_value(board_id: {board_id}, item_id: {item_id}, column_id: "{column_id}", value: "{value_escaped}") {{ id }} }}'

        response = requests.post(url, headers=headers, json={"query": query})

        if response.status_code == 200:
            resp_data = response.json()
            if "errors" not in resp_data:
                print(f"[MONDAY] Colonne texte {column_id} mise à jour avec succès")
                return True
            else:
                print(f"[MONDAY ERROR] Erreur mise à jour colonne texte: {resp_data['errors']}")
                return False
        else:
            print(f"[MONDAY ERROR] HTTP {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"[MONDAY ERROR] Exception mise à jour colonne texte: {e}")
        return False


def find_monday_item_by_soumission(username: str, soumission_num: str) -> Optional[str]:
    """
    Trouve l'ID d'un item Monday.com par son numéro de soumission

    Args:
        username: Username de l'entrepreneur
        soumission_num: Numéro de soumission à rechercher

    Returns:
        Optional[str]: ID de l'item Monday si trouvé, None sinon
    """
    import os
    import json

    api_key, board_id = get_monday_credentials(username)

    if not api_key or not board_id:
        print(f"[MONDAY] Pas de configuration Monday.com pour {username}")
        return None

    # Charger les données du client pour avoir prenom et nom
    prenom = None
    nom = None
    # Utilise la variable globale base_cloud définie en haut du fichier

    for category in ["acceptees", "produit"]:
        fichier = os.path.join(f"{base_cloud}/ventes_{category}", username, "ventes.json")
        if os.path.exists(fichier):
            try:
                with open(fichier, "r", encoding="utf-8") as f:
                    ventes = json.load(f)
                for v in ventes:
                    if v.get("num") == soumission_num:
                        prenom = v.get("prenom") or v.get("clientPrenom", "")
                        nom = v.get("nom") or v.get("clientNom", "")
                        print(f"[MONDAY DEBUG] Trouvé client: prenom='{prenom}', nom='{nom}', num='{soumission_num}'")
                        break
                if prenom and nom:
                    break
            except Exception as e:
                print(f"[MONDAY] Erreur lecture {fichier}: {e}")

    if not prenom or not nom:
        print(f"[MONDAY DEBUG] Aucun prenom/nom trouvé pour num={soumission_num}")

    return find_existing_monday_item(api_key, board_id, soumission_num, prenom, nom)


def sync_vente_to_monday(username: str, vente_data: Dict) -> bool:
    """
    Synchronise une vente acceptée vers Monday.com

    Args:
        username: Username de l'entrepreneur
        vente_data: Données de la vente acceptée

    Returns:
        bool: True si succès ou si pas de config Monday.com, False en cas d'erreur
    """
    # Récupérer les credentials Monday.com
    api_key, board_id = get_monday_credentials(username)

    if not api_key or not board_id:
        print(f"[MONDAY] Synchronisation ignorée - pas de configuration Monday.com pour {username}")
        return True  # Pas une erreur, juste pas configuré

    # Créer l'item dans Monday.com (avec username pour le système de ban)
    success = create_monday_item(api_key, board_id, vente_data, username)

    if success:
        print(f"[MONDAY] Vente synchronisee avec succes vers Monday.com")
    else:
        print(f"[MONDAY] Echec de la synchronisation vers Monday.com")

    return success
