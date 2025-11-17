#!/usr/bin/env python3
"""
Script pour créer tous les utilisateurs de Qwota
À exécuter une seule fois sur Render via: python create_users.py
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(__file__))

from database import create_user

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

def main():
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
