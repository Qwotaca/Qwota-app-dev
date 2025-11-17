"""
Script de test Google OAuth2
Verifie si la configuration est correcte
"""

import os
from dotenv import load_dotenv

# Charger .env
load_dotenv()

print("=" * 60)
print("TEST CONFIGURATION GOOGLE OAUTH2")
print("=" * 60)
print()

# 1. Verifier variables d'environnement
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GMAIL_REDIRECT_URI = os.getenv("GMAIL_REDIRECT_URI")

print("[1] VARIABLES D'ENVIRONNEMENT")
print("-" * 60)
print(f"CLIENT_ID: {CLIENT_ID[:30]}..." if CLIENT_ID else "CLIENT_ID: [NON DEFINI]")
print(f"CLIENT_SECRET: {CLIENT_SECRET[:20]}..." if CLIENT_SECRET else "CLIENT_SECRET: [NON DEFINI]")
print(f"REDIRECT_URI: {REDIRECT_URI}" if REDIRECT_URI else "REDIRECT_URI: [NON DEFINI]")
print(f"GMAIL_REDIRECT_URI: {GMAIL_REDIRECT_URI}" if GMAIL_REDIRECT_URI else "GMAIL_REDIRECT_URI: [NON DEFINI]")
print()

if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    print("[ERREUR] Variables d'environnement manquantes !")
    print("Verifiez votre fichier .env")
    exit(1)

print("[OK] Toutes les variables sont definies")
print()

# 2. Construire l'URL OAuth2
SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send"
]

oauth_url = (
    f"https://accounts.google.com/o/oauth2/v2/auth?"
    f"client_id={CLIENT_ID}&"
    f"redirect_uri={REDIRECT_URI}&"
    f"response_type=code&"
    f"scope={' '.join(SCOPES)}&"
    f"access_type=offline&"
    f"prompt=consent"
)

print("[2] URL OAUTH2 GENEREE")
print("-" * 60)
print(f"URL: {oauth_url[:100]}...")
print()

# 3. URI de redirection attendues
print("[3] URI DE REDIRECTION A CONFIGURER DANS GOOGLE CLOUD CONSOLE")
print("-" * 60)
print()
print("Allez sur: https://console.cloud.google.com/apis/credentials")
print("Editez votre Client ID OAuth 2.0")
print()
print("Ajoutez ces URI dans 'URI de redirection autorises':")
print()
print("   http://localhost:8080/oauth2callback")
print("   http://localhost:8080/gmail/callback")
print("   http://127.0.0.1:8080/oauth2callback")
print("   http://127.0.0.1:8080/gmail/callback")
print()

# 4. APIs a activer
print("[4] APIs A ACTIVER DANS GOOGLE CLOUD CONSOLE")
print("-" * 60)
print()
print("Allez sur: https://console.cloud.google.com/apis/library")
print()
print("Activez ces APIs:")
print("   1. Google Calendar API")
print("   2. Gmail API")
print("   3. Google People API (optionnel)")
print()

# 5. Scopes a configurer
print("[5] SCOPES A CONFIGURER DANS L'ECRAN DE CONSENTEMENT")
print("-" * 60)
print()
print("Allez sur: https://console.cloud.google.com/apis/credentials/consent")
print()
print("Dans 'Champs d'application', ajoutez:")
print()
for scope in SCOPES:
    print(f"   {scope}")
print()

# 6. Test de connexion
print("[6] TEST DE CONNEXION")
print("-" * 60)
print()
print("Pour tester la connexion Google:")
print()
print("1. Assurez-vous que le serveur tourne:")
print("   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080")
print()
print("2. Ouvrez votre navigateur:")
print("   http://localhost:8080/apppc")
print()
print("3. Connectez-vous avec:")
print("   Username: mathis")
print("   Password: test123")
print()
print("4. Cliquez sur 'Connecter Google' ou 'Connecter Gmail'")
print()
print("5. Si vous voyez une page Google (pas d'erreur 400), c'est bon !")
print()

print("=" * 60)
print("DIAGNOSTIC TERMINE")
print("=" * 60)
print()
print("Si vous voyez toujours l'erreur 400 apres avoir configure")
print("Google Cloud Console, attendez 5-10 minutes (propagation)")
print("puis redemarrez le serveur.")
print()
