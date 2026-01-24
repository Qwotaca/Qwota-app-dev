"""
Script rapide pour ajouter un utilisateur
Usage: python add_user.py
"""

from database import create_user

# MODIFIE CES VALEURS ICI:
username = "nouveau_user"      # Change le username
password = "motdepasse123"     # Change le mot de passe
role = "entrepreneur"          # Choix: entrepreneur, coach, direction, beta

# Créer l'utilisateur
if create_user(username, password, role):
    print(f"\n[OK] Utilisateur '{username}' cree avec succes!")
    print(f"     Role: {role}")
    print(f"\nIl peut maintenant se connecter avec:")
    print(f"     Username: {username}")
    print(f"     Password: {password}")
else:
    print(f"\n[ERREUR] Impossible de creer l'utilisateur '{username}'")
    print("     Il existe peut-etre deja?")
