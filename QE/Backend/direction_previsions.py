"""
Direction Team Objectifs - Gestion des prévisions d'objectifs par direction pour les coaches
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Déterminer le chemin de base selon l'OS
if sys.platform == 'win32':
    # Windows - remonter à la racine du projet (3 niveaux depuis QE/Backend/direction_previsions.py)
    DATA_DIR = Path(__file__).parent.parent.parent / "data" / "direction_previsions"
else:
    # Unix/Linux (Production sur Render)
    # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
    DATA_DIR = Path(base_cloud) / "direction_previsions"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_direction_previsions_file(direction_username):
    """
    Retourne le chemin du fichier JSON des prévisions pour un utilisateur direction
    """
    return DATA_DIR / f"{direction_username}_previsions.json"


def load_direction_previsions(direction_username):
    """
    Charge les prévisions d'objectifs d'un utilisateur direction pour ses coaches

    Args:
        direction_username: Nom d'utilisateur de la direction

    Returns:
        dict: Dictionnaire {coach_username: objectif_prevision}
    """
    file_path = get_direction_previsions_file(direction_username)

    if not file_path.exists():
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('previsions', {})
    except Exception as e:
        print(f"[DIRECTION PREVISIONS] Erreur lecture {direction_username}: {e}")
        return {}


def save_direction_previsions(direction_username, previsions):
    """
    Sauvegarde les prévisions d'objectifs d'un utilisateur direction pour ses coaches

    Args:
        direction_username: Nom d'utilisateur de la direction
        previsions: Dictionnaire {coach_username: objectif_prevision}

    Returns:
        bool: True si succès, False sinon
    """
    file_path = get_direction_previsions_file(direction_username)

    try:
        print(f"[DIRECTION PREVISIONS] Tentative sauvegarde pour {direction_username}")
        print(f"[DIRECTION PREVISIONS] Chemin fichier: {file_path}")
        print(f"[DIRECTION PREVISIONS] Répertoire DATA_DIR: {DATA_DIR}")
        print(f"[DIRECTION PREVISIONS] Existe: {DATA_DIR.exists()}")
        print(f"[DIRECTION PREVISIONS] Prévisions: {previsions}")

        data = {
            'direction_username': direction_username,
            'previsions': previsions,
            'last_updated': datetime.now().isoformat()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[DIRECTION PREVISIONS] OK Sauvegarde pour {direction_username}: {len(previsions)} previsions")
        return True

    except Exception as e:
        print(f"[DIRECTION PREVISIONS] ERREUR sauvegarde {direction_username}: {e}")
        print(f"[DIRECTION PREVISIONS] Type erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def get_direction_team_objectif_total(direction_username):
    """
    Calcule le total des prévisions d'objectifs pour tous les coaches

    Args:
        direction_username: Nom d'utilisateur de la direction

    Returns:
        float: Total des prévisions
    """
    previsions = load_direction_previsions(direction_username)
    total = sum(float(objectif) for objectif in previsions.values())
    return total


# ========== GESTION DES MÉTRIQUES (CM, RATIO MARKETING, TAUX DE VENTE) ==========

def get_direction_metrics_file(direction_username):
    """
    Retourne le chemin du fichier JSON des métriques pour un utilisateur direction
    """
    return DATA_DIR / f"{direction_username}_metrics.json"


def load_direction_metrics(direction_username):
    """
    Charge les métriques d'équipe d'un utilisateur direction (valeur unique)

    Args:
        direction_username: Nom d'utilisateur de la direction

    Returns:
        dict: Dictionnaire {cm: X, ratioMktg: Y, tauxVente: Z}
    """
    file_path = get_direction_metrics_file(direction_username)

    if not file_path.exists():
        return {'cm': 0, 'ratioMktg': 0, 'tauxVente': 0}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('metrics', {'cm': 0, 'ratioMktg': 0, 'tauxVente': 0})
    except Exception as e:
        print(f"[DIRECTION METRICS] Erreur lecture {direction_username}: {e}")
        return {'cm': 0, 'ratioMktg': 0, 'tauxVente': 0}


def save_direction_metrics(direction_username, metrics):
    """
    Sauvegarde les métriques d'équipe d'un utilisateur direction (valeur unique)

    Args:
        direction_username: Nom d'utilisateur de la direction
        metrics: Dictionnaire {cm: X, ratioMktg: Y, tauxVente: Z}

    Returns:
        bool: True si succès, False sinon
    """
    file_path = get_direction_metrics_file(direction_username)

    try:
        print(f"[DIRECTION METRICS] Tentative sauvegarde pour {direction_username}")
        print(f"[DIRECTION METRICS] Chemin fichier: {file_path}")
        print(f"[DIRECTION METRICS] Métriques: {metrics}")

        data = {
            'direction_username': direction_username,
            'metrics': metrics,
            'last_updated': datetime.now().isoformat()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[DIRECTION METRICS] OK Sauvegarde pour {direction_username}: CM={metrics.get('cm')}, Ratio={metrics.get('ratioMktg')}%, Taux={metrics.get('tauxVente')}%")
        return True

    except Exception as e:
        print(f"[DIRECTION METRICS] ERREUR sauvegarde {direction_username}: {e}")
        print(f"[DIRECTION METRICS] Type erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
