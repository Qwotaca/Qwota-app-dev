"""
🔄 SCRIPT DE MIGRATION - Transfert des utilisateurs vers SQLite
Exécute ce script UNE SEULE FOIS pour migrer les utilisateurs
"""

import sys
import os

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, os.path.dirname(__file__))

from database import init_database, migrate_users_from_dict, get_user_stats, list_all_users
import bcrypt


# 🔐 Fonction de hashage (identique à main.py)
def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# 👥 UTILISATEURS EXISTANTS (copié depuis main.py)
users = {
    "admin": {"password": hash_password("admin99!."), "role": "direction"},
    "mathis": {"password": hash_password("test123"), "role": "entrepreneur"},
    "fboucher": {"password": hash_password("20050613"), "role": "entrepreneur"},
    "coach01": {"password": hash_password("coachpass"), "role": "coach"},
    "direction": {"password": hash_password("direction123!"), "role": "direction"},

    # 🧪 Comptes BETA
    "lsauriol": {"password": hash_password("Qualite101!"), "role": "beta"},
    "mfiset": {"password": hash_password("Qualite102!"), "role": "beta"},
    "asactouris": {"password": hash_password("Qualite103!"), "role": "beta"},
    "paudibert": {"password": hash_password("Qualite104!"), "role": "beta"},
    "parioux": {"password": hash_password("Qualite105!"), "role": "beta"},
    "jjulien": {"password": hash_password("Qualite106!"), "role": "beta"},
    "cdupuis": {"password": hash_password("Qualite107!"), "role": "beta"},
    "bdauvergne": {"password": hash_password("Qualite108!"), "role": "beta"},
    "asoucy": {"password": hash_password("Qualite109!"), "role": "beta"},
    "apaquette": {"password": hash_password("Qualite110!"), "role": "beta"},
    "naubin": {"password": hash_password("Qualite111!"), "role": "beta"},
    "elavgine": {"password": hash_password("Qualite100!"), "role": "beta"}
}


def main():
    """Exécute la migration complète"""
    print("=" * 60)
    print("MIGRATION VERS BASE DE DONNEES SQLite")
    print("=" * 60)

    # Étape 1: Initialiser la base de données
    print("\nEtape 1: Initialisation de la base de donnees...")
    init_database()

    # Étape 2: Migrer les utilisateurs
    print("\nEtape 2: Migration des utilisateurs...")
    migrate_users_from_dict(users)

    # Étape 3: Vérifier les résultats
    print("\nEtape 3: Verification...")
    stats = get_user_stats()
    print(f"\nStatistiques finales:")
    print(f"   - Total utilisateurs: {stats['total']}")
    print(f"   - Par role:")
    for role, count in stats['by_role'].items():
        print(f"      * {role}: {count}")

    # Étape 4: Liste des utilisateurs
    print("\nListe des utilisateurs migres:")
    all_users = list_all_users()
    for user in all_users:
        print(f"   - {user['username']:15} | Role: {user['role']:15} | Cree: {user['created_at']}")

    print("\n" + "=" * 60)
    print("MIGRATION TERMINEE AVEC SUCCES !")
    print("=" * 60)
    print("\nProchaine etape: Redemarrer le serveur pour utiliser la nouvelle base de donnees")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERREUR lors de la migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
