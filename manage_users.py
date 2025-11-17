"""
Script de gestion des utilisateurs Qwota
Usage: python manage_users.py
"""

from database import (
    create_user, list_all_users, update_user_password,
    change_user_role, delete_user, get_user_stats
)

def menu():
    print("\n" + "="*50)
    print("GESTION DES UTILISATEURS QWOTA")
    print("="*50)
    print("\n1. Lister tous les utilisateurs")
    print("2. Ajouter un utilisateur")
    print("3. Changer le mot de passe")
    print("4. Changer le role")
    print("5. Desactiver un utilisateur")
    print("6. Voir les statistiques")
    print("0. Quitter")

    choice = input("\nChoix: ")
    return choice

def main():
    while True:
        choice = menu()

        if choice == "1":
            users = list_all_users()
            print("\nUtilisateurs actifs:")
            for user in users:
                print(f"  - {user['username']:15} | Role: {user['role']:15} | Cree: {user['created_at']}")

        elif choice == "2":
            username = input("Username: ")
            password = input("Mot de passe: ")
            print("\nRoles disponibles: entrepreneur, coach, direction, beta")
            role = input("Role: ")

            if create_user(username, password, role):
                print(f"[OK] Utilisateur '{username}' cree")
            else:
                print("[ERREUR] Echec de la creation")

        elif choice == "3":
            username = input("Username: ")
            new_password = input("Nouveau mot de passe: ")

            if update_user_password(username, new_password):
                print("[OK] Mot de passe mis a jour")
            else:
                print("[ERREUR] Utilisateur non trouve")

        elif choice == "4":
            username = input("Username: ")
            print("\nRoles disponibles: entrepreneur, coach, direction, beta")
            new_role = input("Nouveau role: ")

            if change_user_role(username, new_role):
                print("[OK] Role mis a jour")
            else:
                print("[ERREUR] Echec de la mise a jour")

        elif choice == "5":
            username = input("Username a desactiver: ")
            confirm = input(f"Confirmer la desactivation de '{username}' (o/n): ")

            if confirm.lower() == 'o':
                if delete_user(username):
                    print("[OK] Utilisateur desactive")
                else:
                    print("[ERREUR] Echec de la desactivation")

        elif choice == "6":
            stats = get_user_stats()
            print(f"\nTotal utilisateurs: {stats['total']}")
            print("Par role:")
            for role, count in stats['by_role'].items():
                print(f"  - {role}: {count}")

        elif choice == "0":
            print("\nAu revoir!")
            break

        else:
            print("\n[ERREUR] Choix invalide")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterruption - Au revoir!")
