#!/usr/bin/env python3
"""
Script pour resynchroniser les RPO de tous les entrepreneurs
Usage: python scripts/sync_all_rpo.py
"""

import sys
import os

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database import get_database_path
from QE.Backend.rpo import sync_soumissions_to_rpo, sync_coach_rpo, sync_direction_rpo


def get_all_entrepreneurs():
    """Récupère tous les entrepreneurs actifs"""
    DB_PATH = get_database_path()
    entrepreneurs = []

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role='entrepreneur' AND is_active=1")
        entrepreneurs = [row[0] for row in cursor.fetchall()]

    return entrepreneurs


def get_all_coaches():
    """Récupère tous les coaches actifs"""
    DB_PATH = get_database_path()
    coaches = []

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role='coach' AND is_active=1")
        coaches = [row[0] for row in cursor.fetchall()]

    return coaches


def main():
    print("=" * 60)
    print("RESYNCHRONISATION DES RPO - TOUS LES ENTREPRENEURS")
    print("=" * 60)
    print()

    # 1. Récupérer tous les entrepreneurs
    entrepreneurs = get_all_entrepreneurs()
    print(f"[INFO] {len(entrepreneurs)} entrepreneurs actifs trouvés")
    print()

    # 2. Synchroniser chaque entrepreneur
    success_count = 0
    error_count = 0

    for i, username in enumerate(entrepreneurs, 1):
        print(f"[{i}/{len(entrepreneurs)}] Synchronisation de {username}...")

        try:
            result = sync_soumissions_to_rpo(username)
            if result:
                print(f"  ✅ {username} - RPO synchronisé avec succès")
                success_count += 1
            else:
                print(f"  ❌ {username} - Échec de la synchronisation")
                error_count += 1
        except Exception as e:
            print(f"  ❌ {username} - Erreur: {e}")
            error_count += 1

        print()

    # 3. Synchroniser les coaches
    print("-" * 60)
    print("SYNCHRONISATION DES COACHES")
    print("-" * 60)

    coaches = get_all_coaches()
    print(f"[INFO] {len(coaches)} coaches actifs trouvés")

    for coach in coaches:
        print(f"  Synchronisation coach {coach}...")
        try:
            sync_coach_rpo(coach)
            print(f"  ✅ Coach {coach} synchronisé")
        except Exception as e:
            print(f"  ❌ Coach {coach} - Erreur: {e}")

    print()

    # 4. Synchroniser la direction
    print("-" * 60)
    print("SYNCHRONISATION DIRECTION")
    print("-" * 60)

    try:
        sync_direction_rpo()
        print("  ✅ Direction synchronisée")
    except Exception as e:
        print(f"  ❌ Direction - Erreur: {e}")

    # 5. Résumé
    print()
    print("=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"  Entrepreneurs traités: {len(entrepreneurs)}")
    print(f"  ✅ Succès: {success_count}")
    print(f"  ❌ Erreurs: {error_count}")
    print(f"  Coaches synchronisés: {len(coaches)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
