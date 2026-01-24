"""
Script pour vider TOUTES les données du backend Qwota
ATTENTION: Cette opération est IRRÉVERSIBLE!
"""

import sqlite3
import os
import json
import shutil
from pathlib import Path

def reset_sqlite_db(db_path):
    """Vide toutes les tables d'une base de données SQLite"""
    if not os.path.exists(db_path):
        print(f"[WARN]  Base de données non trouvée: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Obtenir toutes les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Vider chaque table
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Ne pas toucher à la table système
                cursor.execute(f"DELETE FROM {table_name};")
                print(f"  [OK] Table vidée: {table_name}")

        # Réinitialiser les auto-increment
        cursor.execute("DELETE FROM sqlite_sequence;")

        conn.commit()
        conn.close()
        print(f"[OK] Base de données vidée: {db_path}\n")
    except Exception as e:
        print(f"[ERR] Erreur avec {db_path}: {e}\n")

def reset_json_files(directory):
    """Réinitialise les fichiers JSON dans un répertoire"""
    if not os.path.exists(directory):
        print(f"[WARN]  Répertoire non trouvé: {directory}")
        return

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                try:
                    # Réinitialiser avec un objet vide ou un tableau vide
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump({}, f, indent=2)
                    print(f"  [OK] Fichier JSON réinitialisé: {file_path}")
                except Exception as e:
                    print(f"  [ERR] Erreur avec {file_path}: {e}")

def main():
    print("=" * 80)
    print("ATTENTION: REINITIALISATION COMPLETE DU BACKEND QWOTA")
    print("=" * 80)
    print("\nCette operation va:")
    print("  - Vider TOUTES les bases de donnees SQLite")
    print("  - Reinitialiser TOUS les fichiers JSON")
    print("  - Supprimer TOUTES les donnees utilisateur")
    print("\nCETTE OPERATION EST IRREVERSIBLE!\n")

    # Demander confirmation
    confirmation = input("Tapez 'OUI' en majuscules pour confirmer: ")
    if confirmation != "OUI":
        print("\nOperation annulee.")
        return

    print("\n" + "=" * 80)
    print("DEBUT DE LA REINITIALISATION")
    print("=" * 80 + "\n")

    # 1. Vider les bases de données SQLite
    print("VIDAGE DES BASES DE DONNEES SQLITE\n")
    databases = [
        "cloud/qwota.db",
        "data/gamification.db",
        "data/qwota.db",
        "data/qwota_users.db",
        "data/users.db"
    ]

    for db in databases:
        reset_sqlite_db(db)

    # 2. Réinitialiser les fichiers JSON
    print("\nREINITIALISATION DES FICHIERS JSON\n")
    reset_json_files("data")

    # 3. Vider les dossiers spécifiques
    print("\nNETTOYAGE DES DOSSIERS SPECIFIQUES\n")

    # Vider le dossier factures (sauf used_nums.json qui sera réinitialisé)
    factures_dir = "factures"
    if os.path.exists(factures_dir):
        for file in os.listdir(factures_dir):
            file_path = os.path.join(factures_dir, file)
            if file.endswith('.pdf'):
                os.remove(file_path)
                print(f"  [OK] Facture supprimée: {file}")

        # Réinitialiser used_nums.json
        used_nums_path = os.path.join(factures_dir, "used_nums.json")
        if os.path.exists(used_nums_path):
            with open(used_nums_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
            print(f"  [OK] used_nums.json réinitialisé\n")

    print("=" * 80)
    print("REINITIALISATION COMPLETE TERMINEE!")
    print("=" * 80)
    print("\nToutes les donnees ont ete videes.")
    print("Le backend est maintenant dans un etat vierge.\n")

if __name__ == "__main__":
    main()
