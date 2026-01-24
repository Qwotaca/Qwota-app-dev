"""
Script de migration des utilisateurs hardcodes vers SQLite
Migre les 17 utilisateurs de main.py vers la base de donnees qwota.db
"""

import sys
import os

# Forcer l'encodage UTF-8 sur Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from database import init_database, create_user, get_user, list_all_users, get_user_stats
from QE.Backend.auth import hash_password

def migrate_users():
    """Migre tous les utilisateurs hardcodes vers SQLite"""

    print("=" * 60)
    print("MIGRATION DES UTILISATEURS VERS SQLITE")
    print("=" * 60)
    print()

    # Initialiser la base de donnees
    print("[INIT] Initialisation de la base de donnees...")
    init_database()
    print()

    # Definir les utilisateurs a migrer (depuis main.py lignes 306-326)
    users_to_migrate = {
        # Comptes principaux
        "admin": {"password": "admin99!.", "role": "direction"},
        "mathis": {"password": "test123", "role": "entrepreneur"},
        "fboucher": {"password": "20050613", "role": "entrepreneur"},
        "coach01": {"password": "coachpass", "role": "coach"},
        "direction": {"password": "direction123!", "role": "direction"},

        # Comptes BETA (acces restreint)
        "lsauriol": {"password": "Qualite101!", "role": "beta"},
        "mfiset": {"password": "Qualite102!", "role": "beta"},
        "asactouris": {"password": "Qualite103!", "role": "beta"},
        "paudibert": {"password": "Qualite104!", "role": "beta"},
        "parioux": {"password": "Qualite105!", "role": "beta"},
        "jjulien": {"password": "Qualite106!", "role": "beta"},
        "cdupuis": {"password": "Qualite107!", "role": "beta"},
        "bdauvergne": {"password": "Qualite108!", "role": "beta"},
        "asoucy": {"password": "Qualite109!", "role": "beta"},
        "apaquette": {"password": "Qualite110!", "role": "beta"},
        "naubin": {"password": "Qualite111!", "role": "beta"},
        "elavgine": {"password": "Qualite100!", "role": "beta"}
    }

    print(f"[INFO] {len(users_to_migrate)} utilisateurs a migrer")
    print()

    # Statistiques
    success_count = 0
    skip_count = 0
    error_count = 0

    # Migrer chaque utilisateur
    for username, user_data in users_to_migrate.items():
        # Vérifier si l'utilisateur existe déjà
        existing_user = get_user(username)

        if existing_user:
            print(f"[SKIP] {username:15} -> Deja existant (role: {existing_user['role']})")
            skip_count += 1
            continue

        # Creer l'utilisateur
        success = create_user(
            username=username,
            password=user_data["password"],  # create_user hashera le mot de passe
            role=user_data["role"],
            email=None
        )

        if success:
            print(f"[OK]   {username:15} -> Migre avec succes (role: {user_data['role']})")
            success_count += 1
        else:
            print(f"[ERR]  {username:15} -> Erreur lors de la migration")
            error_count += 1

    print()
    print("=" * 60)
    print("RESUME DE LA MIGRATION")
    print("=" * 60)
    print(f"[OK]   Migres avec succes : {success_count}")
    print(f"[SKIP] Deja existants     : {skip_count}")
    print(f"[ERR]  Erreurs            : {error_count}")
    print(f"[INFO] Total              : {len(users_to_migrate)}")
    print()

    # Afficher les statistiques de la base
    stats = get_user_stats()
    print("=" * 60)
    print("STATISTIQUES DE LA BASE DE DONNEES")
    print("=" * 60)
    print(f"Total utilisateurs actifs : {stats['total']}")
    print()
    print("Par role:")
    for role, count in stats['by_role'].items():
        print(f"   - {role:15} : {count} utilisateur(s)")
    print()

    # Lister tous les utilisateurs
    print("=" * 60)
    print("LISTE DES UTILISATEURS")
    print("=" * 60)
    all_users = list_all_users()
    for user in all_users:
        print(f"   - {user['username']:15} | Role: {user['role']:15} | Cree: {user['created_at'][:10]}")
    print()

    print("=" * 60)
    print("MIGRATION TERMINEE")
    print("=" * 60)
    print()
    print("Prochaines etapes:")
    print("   1. Verifier que tous les utilisateurs sont bien crees")
    print("   2. Tester la connexion avec un utilisateur")
    print("   3. Supprimer le dictionnaire 'users' de main.py")
    print("   4. Redemarrer le serveur")
    print()


if __name__ == "__main__":
    try:
        migrate_users()
    except Exception as e:
        print(f"\n[ERREUR CRITIQUE] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
