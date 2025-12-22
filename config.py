"""
Configuration centralisée de l'application Qwota
Charge les variables d'environnement et définit les constantes
"""
import os
from datetime import timedelta
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
BASE_CLOUD_PATH = os.getenv('BASE_CLOUD_PATH', 'data')

# Sécurité
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '10080'))

# Mots de passe par défaut pour les comptes admin (à changer en production!)
SUPPORT_DEFAULT_PASSWORD = os.getenv('SUPPORT_DEFAULT_PASSWORD', 'Support@2025')
DIRECTION_DEFAULT_PASSWORD = os.getenv('DIRECTION_DEFAULT_PASSWORD', 'Direction@2025')

# Validation de la clé secrète en production
ENV = os.getenv('ENV', 'development')
if ENV == 'production' and JWT_SECRET_KEY == 'dev-secret-key-CHANGE-IN-PRODUCTION':
    raise ValueError("ERREUR: JWT_SECRET_KEY doit être défini en production!")

# Base de données
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/qwota.db')

# CORS
ALLOWED_ORIGINS_STR = os.getenv('ALLOWED_ORIGINS', 'http://localhost:8080,http://localhost:3000')
ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in ALLOWED_ORIGINS_STR.split(',')]

# Application
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8080'))

# Limites
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '5'))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_UPLOAD_FILES = int(os.getenv('MAX_UPLOAD_FILES', '10'))
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
LOGIN_RATE_LIMIT_PER_MINUTE = int(os.getenv('LOGIN_RATE_LIMIT_PER_MINUTE', '5'))

# Session & Cookies
COOKIE_MAX_AGE_DAYS = int(os.getenv('COOKIE_MAX_AGE_DAYS', '7'))
COOKIE_MAX_AGE_SECONDS = int(timedelta(days=COOKIE_MAX_AGE_DAYS).total_seconds())
SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'qwota_session')

# Sécurité des cookies (strict en production)
COOKIE_SECURE = ENV == 'production'  # HTTPS uniquement en production
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = 'strict' if ENV == 'production' else 'lax'

# Formats de date/heure
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
DATE_FORMAT = "%Y-%m-%d"
DATETIME_ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"

# Extensions de fichiers autorisées
ALLOWED_FILE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx'}

# Rôles utilisateur
USER_ROLES = {'entrepreneur', 'coach', 'direction', 'support', 'beta'}

# Chemins de dossiers requis
REQUIRED_DIRECTORIES = [
    "accounts", "blacklist", "chiffre_affaires", "clients_perdus",
    "emails", "employes", "equipe", "factures_completes",
    "facturation_qe_historique", "facturation_qe_statuts",
    "facturations_en_cours", "facturations_traitees", "facturations_urgentes",
    "ficheremployer", "ficherlegal", "fichermarketing", "ficherprocessus",
    "gqp", "gqp_images", "pdfcalcul", "prospects", "projects",
    "reviews", "signatures", "soumissions_completes", "soumissions_signees",
    "support_attachments", "themes", "tokens", "total_signees",
    "travaux_a_completer", "travaux_completes", "ventes_acceptees",
    "ventes_attente", "ventes_produit"
]

def get_cloud_path(*paths) -> Path:
    """Retourne un chemin sécurisé dans le cloud storage"""
    return Path(BASE_CLOUD_PATH).joinpath(*paths)

def validate_config():
    """Valide la configuration au démarrage"""
    errors = []

    if ENV == 'production':
        if JWT_SECRET_KEY == 'dev-secret-key-CHANGE-IN-PRODUCTION':
            errors.append("JWT_SECRET_KEY must be set in production")

        if len(JWT_SECRET_KEY) < 32:
            errors.append("JWT_SECRET_KEY must be at least 32 characters")

        if DEBUG:
            errors.append("DEBUG must be false in production")

        if 'localhost' in ALLOWED_ORIGINS_STR:
            errors.append("localhost should not be in ALLOWED_ORIGINS in production")

    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True
