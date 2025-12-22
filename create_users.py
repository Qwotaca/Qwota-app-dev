#!/usr/bin/env python3
"""
Script pour créer tous les utilisateurs de Qwota
À exécuter une seule fois sur Render via: python create_users.py

Options:
  --delete-all : Supprime tous les utilisateurs avant de créer
"""

import sys
import os
import sqlite3

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(__file__))

from database import create_user, get_database_path

# Liste de tous les utilisateurs à créer
USERS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "mathis", "password": "mathis123", "role": "entrepreneur"},
    {"username": "fboucher", "password": "fboucher123", "role": "entrepreneur"},
    {"username": "coach01", "password": "coach123", "role": "coach"},
    {"username": "direction", "password": "direction123", "role": "direction"},
    {"username": "lsauriol", "password": "lsauriol123", "role": "entrepreneur"},
    {"username": "mfiset", "password": "mfiset123", "role": "entrepreneur"},
    {"username": "asactouris", "password": "asactouris123", "role": "entrepreneur"},
    {"username": "paudibert", "password": "paudibert123", "role": "entrepreneur"},
    {"username": "parioux", "password": "parioux123", "role": "entrepreneur"},
    {"username": "jjulien", "password": "jjulien123", "role": "entrepreneur"},
    {"username": "cdupuis", "password": "cdupuis123", "role": "entrepreneur"},
    {"username": "bdauvergne", "password": "bdauvergne123", "role": "entrepreneur"},
    {"username": "asoucy", "password": "asoucy123", "role": "entrepreneur"},
    {"username": "apaquette", "password": "apaquette123", "role": "entrepreneur"},
    {"username": "naubin", "password": "naubin123", "role": "entrepreneur"},
    {"username": "elavgine", "password": "elavgine123", "role": "entrepreneur"},
    {"username": "test", "password": "test123", "role": "entrepreneur"},
    {"username": "test_guide", "password": "test123", "role": "entrepreneur"},
    {"username": "support", "password": "support123", "role": "admin"},
]

def delete_all_users():
    """Supprime tous les utilisateurs de la base de données"""
    db_path = get_database_path()
    print(f"[DELETE_USERS] Suppression de tous les utilisateurs de {db_path}...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.execute('DELETE FROM users')
        conn.commit()
        conn.close()
        print(f"[DELETE_USERS] ✓ {count} utilisateur(s) supprimé(s)")
        return True
    except Exception as e:
        print(f"[DELETE_USERS] ✗ Erreur: {e}")
        return False

def main():
    # Vérifier si l'option --delete-all est présente
    if '--delete-all' in sys.argv:
        if not delete_all_users():
            print("[CREATE_USERS] Abandon suite à l'erreur de suppression")
            return
        print()

    print(f"[CREATE_USERS] Création de {len(USERS)} utilisateurs...")

    created = 0
    skipped = 0

    for user in USERS:
        try:
            success = create_user(
                username=user["username"],
                password=user["password"],
                role=user["role"]
            )

            if success:
                print(f"✓ Utilisateur '{user['username']}' créé avec succès")
                created += 1
            else:
                print(f"⚠ Utilisateur '{user['username']}' existe déjà")
                skipped += 1

        except Exception as e:
            print(f"✗ Erreur lors de la création de '{user['username']}': {e}")

    print(f"\n[CREATE_USERS] Résultat: {created} créés, {skipped} ignorés")
    print("[CREATE_USERS] Terminé!")

if __name__ == "__main__":
    main()
