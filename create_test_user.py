"""
Script pour créer un compte test pour tester le flux onboarding + guide
"""
import sys
import os

# Ajouter le répertoire parent au path pour importer database
sys.path.insert(0, os.path.dirname(__file__))

from database import init_database, create_user, init_guide_progress

def create_test_account():
    """Crée un compte test nommé 'test_guide'"""

    # Initialiser la base de données (créer les tables si elles n'existent pas)
    print("[DB] Initialisation de la base de donnees...")
    init_database()

    # Informations du compte test
    username = "test_guide"
    password = "Test123!"  # Mot de passe simple pour les tests
    role = "entrepreneur"
    email = "test@qwota.com"

    # Créer l'utilisateur
    print(f"\n[USER] Creation du compte test '{username}'...")
    success = create_user(username, password, role, email)

    if success:
        print(f"[OK] Compte '{username}' cree avec succes!")
        print(f"\n[INFO] Informations de connexion:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print(f"   Role: {role}")

        # Initialiser la progression du guide (optionnel, sera fait auto au premier accès)
        print(f"\n[GUIDE] Initialisation de la progression du guide...")
        init_guide_progress(username)

        print(f"\n[SUCCESS] Le compte est pret a etre teste!")
        print(f"\n[FLOW] Flux de test:")
        print(f"   1. Se connecter avec {username} / {password}")
        print(f"   2. Completer l'onboarding (prenom, nom, etc.)")
        print(f"   3. Visionner les 5 videos du guide")
        print(f"   4. Acceder au dashboard")

    else:
        print(f"[ERROR] Erreur: Le compte '{username}' existe deja ou une erreur s'est produite")
        print(f"   Pour reinitialiser, supprimez d'abord l'utilisateur existant")

if __name__ == "__main__":
    create_test_account()
