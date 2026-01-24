"""
Fonctions utilitaires sécurisées et réutilisables
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

import config

logger = logging.getLogger(__name__)

T = TypeVar('T')

# ===================================
# GESTION SÉCURISÉE DES FICHIERS JSON
# ===================================

def load_json_file(file_path: Union[str, Path], default: Optional[T] = None) -> T:
    """
    Charge un fichier JSON de manière sécurisée

    Args:
        file_path: Chemin du fichier
        default: Valeur par défaut si fichier inexistant ou vide

    Returns:
        Contenu du fichier ou default
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return default if default is not None else []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return default if default is not None else []
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return default if default is not None else []
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        raise

def save_json_file(
    file_path: Union[str, Path],
    data: Any,
    create_dirs: bool = True
) -> bool:
    """
    Sauvegarde des données en JSON de manière sécurisée

    Args:
        file_path: Chemin du fichier
        data: Données à sauvegarder
        create_dirs: Créer les dossiers parents si nécessaire

    Returns:
        True si succès, False sinon
    """
    file_path = Path(file_path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

# ===================================
# VALIDATION ET SÉCURITÉ
# ===================================

def validate_username(username: str) -> bool:
    """
    Valide un nom d'utilisateur

    Args:
        username: Nom d'utilisateur à valider

    Returns:
        True si valide
    """
    if not username or len(username) < 3 or len(username) > 50:
        return False

    # Alphanumériques, underscores et tirets uniquement
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', username))

def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier pour éviter path traversal

    Args:
        filename: Nom de fichier à nettoyer

    Returns:
        Nom de fichier sécurisé
    """
    # Garder uniquement le nom, pas le chemin
    filename = Path(filename).name

    # Remplacer les caractères dangereux
    filename = re.sub(r'[^\w\s.-]', '_', filename)

    # Limiter la longueur
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename

def validate_file_extension(filename: str, allowed_extensions: set = None) -> bool:
    """
    Valide l'extension d'un fichier

    Args:
        filename: Nom du fichier
        allowed_extensions: Extensions autorisées (None = config par défaut)

    Returns:
        True si extension autorisée
    """
    if allowed_extensions is None:
        allowed_extensions = config.ALLOWED_FILE_EXTENSIONS

    ext = Path(filename).suffix.lower()
    return ext in allowed_extensions

def get_safe_path(base_dir: Union[str, Path], *paths: str) -> Path:
    """
    Crée un chemin sécurisé en vérifiant qu'il reste dans base_dir

    Args:
        base_dir: Répertoire de base
        *paths: Composants du chemin

    Returns:
        Chemin sécurisé

    Raises:
        ValueError: Si le chemin sort de base_dir (path traversal)
    """
    base_dir = Path(base_dir).resolve()

    # Nettoyer chaque composant du chemin
    safe_paths = [sanitize_filename(p) for p in paths]

    # Construire le chemin complet
    full_path = base_dir.joinpath(*safe_paths).resolve()

    # Vérifier qu'on reste dans base_dir
    try:
        full_path.relative_to(base_dir)
    except ValueError:
        raise ValueError(f"Path traversal detected: {full_path} is outside {base_dir}")

    return full_path

# ===================================
# VALIDATION DES DONNÉES
# ===================================

def validate_role(role: str) -> bool:
    """Valide un rôle utilisateur"""
    return role in config.USER_ROLES

def validate_email(email: str) -> bool:
    """Valide un email basique"""
    if not email:
        return False

    # Regex basique pour email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valide la force d'un mot de passe

    Args:
        password: Mot de passe à valider

    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"

    if not re.search(r'[A-Z]', password):
        return False, "Le mot de passe doit contenir au moins une majuscule"

    if not re.search(r'[a-z]', password):
        return False, "Le mot de passe doit contenir au moins une minuscule"

    if not re.search(r'[0-9]', password):
        return False, "Le mot de passe doit contenir au moins un chiffre"

    return True, ""

# ===================================
# HELPERS
# ===================================

def normalize_username(username: str) -> str:
    """Normalise un nom d'utilisateur (lowercase, stripped)"""
    return username.strip().lower()

def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """Tronque une chaîne si trop longue"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix
