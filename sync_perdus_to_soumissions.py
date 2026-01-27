#!/usr/bin/env python3
"""
Script pour synchroniser les clients perdus vers soumissions_completes.

Ajoute tous les clients perdus qui ne sont pas déjà dans soumissions_completes.
Fonctionne sur local et Render (utilise base_cloud comme le reste de l'app).

Usage:
    python sync_perdus_to_soumissions.py [username]

    Si username est fourni, synchronise seulement cet utilisateur.
    Sinon, synchronise tous les entrepreneurs.
"""

import os
import json
import sys
from datetime import datetime

# Utiliser la même logique que main.py pour base_cloud
if sys.platform == 'win32':
    # Windows - chemin relatif
    base_cloud = os.path.join(os.path.dirname(__file__), 'data')
else:
    # Unix/Linux (Production sur Render)
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")

print(f"[ENV] base_cloud = {base_cloud}")


def get_all_entrepreneurs():
    """Récupère la liste de tous les entrepreneurs depuis les dossiers clients_perdus"""
    perdus_base = os.path.join(base_cloud, "clients_perdus")
    if not os.path.exists(perdus_base):
        return []

    entrepreneurs = []
    for name in os.listdir(perdus_base):
        path = os.path.join(perdus_base, name)
        if os.path.isdir(path):
            entrepreneurs.append(name)

    return entrepreneurs


def sync_perdus_to_soumissions(username):
    """
    Synchronise les clients perdus vers soumissions_completes pour un utilisateur.

    Returns:
        tuple: (nb_ajoutes, nb_deja_present, nb_total_perdus)
    """
    print(f"\n[SYNC] Traitement de {username}...")

    # Chemins des fichiers
    perdus_file = os.path.join(base_cloud, "clients_perdus", username, "clients.json")
    soumissions_dir = os.path.join(base_cloud, "soumissions_completes", username)
    soumissions_file = os.path.join(soumissions_dir, "soumissions.json")

    # Charger les clients perdus
    if not os.path.exists(perdus_file):
        print(f"  [SKIP] Pas de fichier clients_perdus pour {username}")
        return (0, 0, 0)

    try:
        with open(perdus_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            clients_perdus = json.loads(content) if content else []
    except Exception as e:
        print(f"  [ERROR] Erreur lecture clients_perdus: {e}")
        return (0, 0, 0)

    if not clients_perdus:
        print(f"  [SKIP] Aucun client perdu pour {username}")
        return (0, 0, 0)

    print(f"  [INFO] {len(clients_perdus)} clients perdus trouvés")

    # Charger les soumissions existantes
    os.makedirs(soumissions_dir, exist_ok=True)
    soumissions = []
    if os.path.exists(soumissions_file):
        try:
            with open(soumissions_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                soumissions = json.loads(content) if content else []
        except Exception as e:
            print(f"  [WARNING] Erreur lecture soumissions: {e}")
            soumissions = []

    # Créer un set des identifiants existants (id et num)
    existing_ids = set()
    existing_nums = set()
    for s in soumissions:
        if s.get("id"):
            existing_ids.add(s.get("id"))
        if s.get("num"):
            existing_nums.add(s.get("num"))

    print(f"  [INFO] {len(soumissions)} soumissions existantes")

    # Ajouter les clients perdus manquants
    nb_ajoutes = 0
    nb_deja_present = 0

    for client in clients_perdus:
        client_id = client.get("id")
        client_num = client.get("num")

        # Vérifier si déjà présent
        if client_id in existing_ids or (client_num and client_num in existing_nums):
            nb_deja_present += 1
            continue

        # Créer l'entrée soumission
        # Générer un num si absent
        if not client_num:
            if client_id:
                client_num = f"POT-{client_id[:8]}"
            else:
                client_num = f"POT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        soumission_entry = {
            "id": client_id,
            "num": client_num,
            "nom": client.get("nom") or client.get("clientNom", ""),
            "prenom": client.get("prenom") or client.get("clientPrenom", ""),
            "courriel": client.get("courriel") or client.get("email", ""),
            "telephone": client.get("telephone", ""),
            "adresse": client.get("adresse", ""),
            "date": client.get("date") or client.get("date_perdu", datetime.now().strftime("%d/%m/%Y")),
            "prix": client.get("prix", "0"),
            "endroit": client.get("type_travaux") or client.get("endroit", ""),
            "produit": client.get("produit", ""),
            "statut": "perdu",
            "source": "sync_perdus"
        }

        soumissions.append(soumission_entry)
        existing_ids.add(client_id)
        if client_num:
            existing_nums.add(client_num)

        client_nom = f"{soumission_entry['prenom']} {soumission_entry['nom']}".strip() or "Inconnu"
        print(f"  [+] Ajouté: {client_nom} ({client_num})")
        nb_ajoutes += 1

    # Sauvegarder si des modifications
    if nb_ajoutes > 0:
        try:
            with open(soumissions_file, "w", encoding="utf-8") as f:
                json.dump(soumissions, f, ensure_ascii=False, indent=2)
            print(f"  [OK] {nb_ajoutes} soumissions ajoutées, {nb_deja_present} déjà présentes")
        except Exception as e:
            print(f"  [ERROR] Erreur sauvegarde: {e}")
            return (0, nb_deja_present, len(clients_perdus))
    else:
        print(f"  [OK] Aucun ajout nécessaire ({nb_deja_present} déjà présentes)")

    return (nb_ajoutes, nb_deja_present, len(clients_perdus))


def sync_rpo(username):
    """Synchronise le RPO pour un utilisateur"""
    try:
        # Ajouter le chemin du projet pour les imports
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        from QE.Backend.rpo import sync_soumissions_to_rpo
        sync_soumissions_to_rpo(username)
        print(f"  [RPO] Synchronisé pour {username}")
        return True
    except Exception as e:
        print(f"  [WARNING] Erreur sync RPO: {e}")
        return False


def main():
    print("=" * 60)
    print("SYNC CLIENTS PERDUS -> SOUMISSIONS COMPLETES")
    print("=" * 60)

    # Vérifier si un username spécifique est demandé
    if len(sys.argv) > 1:
        usernames = [sys.argv[1]]
        print(f"[MODE] Utilisateur spécifique: {usernames[0]}")
    else:
        usernames = get_all_entrepreneurs()
        print(f"[MODE] Tous les entrepreneurs ({len(usernames)} trouvés)")

    if not usernames:
        print("[ERROR] Aucun entrepreneur trouvé")
        return

    # Stats globales
    total_ajoutes = 0
    total_deja_present = 0
    total_perdus = 0
    users_modifies = []

    for username in sorted(usernames):
        nb_ajoutes, nb_deja, nb_perdus = sync_perdus_to_soumissions(username)
        total_ajoutes += nb_ajoutes
        total_deja_present += nb_deja
        total_perdus += nb_perdus

        if nb_ajoutes > 0:
            users_modifies.append(username)

    # Sync RPO pour les utilisateurs modifiés
    if users_modifies:
        print("\n" + "=" * 60)
        print("SYNCHRONISATION RPO")
        print("=" * 60)
        for username in users_modifies:
            sync_rpo(username)

    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Entrepreneurs traités: {len(usernames)}")
    print(f"Clients perdus total: {total_perdus}")
    print(f"Déjà dans soumissions: {total_deja_present}")
    print(f"Nouvellement ajoutés: {total_ajoutes}")
    if users_modifies:
        print(f"Utilisateurs modifiés: {', '.join(users_modifies)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
