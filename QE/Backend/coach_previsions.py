"""
Coach Team Objectifs - Gestion des prévisions d'objectifs par coach
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Déterminer le chemin de base selon l'OS
if sys.platform == 'win32':
    # Windows - remonter à la racine du projet (3 niveaux depuis QE/Backend/coach_previsions.py)
    DATA_DIR = Path(__file__).parent.parent.parent / "data" / "coach_previsions"
else:
    # Unix/Linux (Production sur Render)
    # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
    DATA_DIR = Path(base_cloud) / "coach_previsions"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_coach_previsions_file(coach_username):
    """
    Retourne le chemin du fichier JSON des prévisions pour un coach
    """
    return DATA_DIR / f"{coach_username}_previsions.json"


def load_coach_previsions(coach_username):
    """
    Charge les prévisions d'objectifs d'un coach

    Args:
        coach_username: Nom d'utilisateur du coach

    Returns:
        dict: Dictionnaire {entrepreneur_username: objectif_prevision}
    """
    file_path = get_coach_previsions_file(coach_username)

    if not file_path.exists():
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('previsions', {})
    except Exception as e:
        print(f"[COACH PREVISIONS] Erreur lecture {coach_username}: {e}")
        return {}


def save_coach_previsions(coach_username, previsions):
    """
    Sauvegarde les prévisions d'objectifs d'un coach

    Args:
        coach_username: Nom d'utilisateur du coach
        previsions: Dictionnaire {entrepreneur_username: objectif_prevision}

    Returns:
        bool: True si succès, False sinon
    """
    file_path = get_coach_previsions_file(coach_username)

    try:
        data = {
            'coach_username': coach_username,
            'previsions': previsions,
            'last_updated': datetime.now().isoformat()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[COACH PREVISIONS] Sauvegarde OK pour {coach_username}: {len(previsions)} previsions")
        return True

    except Exception as e:
        print(f"[COACH PREVISIONS] ERREUR sauvegarde {coach_username}: {e}")
        return False


def get_team_objectif_total(coach_username):
    """
    Calcule le total des prévisions d'objectifs pour l'équipe d'un coach

    Args:
        coach_username: Nom d'utilisateur du coach

    Returns:
        float: Total des prévisions
    """
    previsions = load_coach_previsions(coach_username)
    total = sum(float(objectif) for objectif in previsions.values())
    return total


# ========== GESTION DES MÉTRIQUES COACH (CM, RATIO MARKETING, TAUX DE VENTE) ==========

def get_coach_metrics_file(coach_username):
    """
    Retourne le chemin du fichier JSON des métriques pour un coach
    """
    return DATA_DIR / f"{coach_username}_metrics.json"


def load_coach_metrics(coach_username):
    """
    Charge les métriques prévisionnelles d'un coach (valeur unique)

    Args:
        coach_username: Nom d'utilisateur du coach

    Returns:
        dict: Dictionnaire {cm: X, ratioMktg: Y, tauxVente: Z}
    """
    file_path = get_coach_metrics_file(coach_username)

    if not file_path.exists():
        return {'cm': 0, 'ratioMktg': 0, 'tauxVente': 0}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('metrics', {'cm': 0, 'ratioMktg': 0, 'tauxVente': 0})
    except Exception as e:
        print(f"[COACH METRICS] Erreur lecture {coach_username}: {e}")
        return {'cm': 0, 'ratioMktg': 0, 'tauxVente': 0}


def save_coach_metrics(coach_username, metrics):
    """
    Sauvegarde les métriques prévisionnelles d'un coach (valeur unique)

    Args:
        coach_username: Nom d'utilisateur du coach
        metrics: Dictionnaire {cm: X, ratioMktg: Y, tauxVente: Z}

    Returns:
        bool: True si succès, False sinon
    """
    file_path = get_coach_metrics_file(coach_username)

    try:
        data = {
            'coach_username': coach_username,
            'metrics': metrics,
            'last_updated': datetime.now().isoformat()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[COACH METRICS] Sauvegarde OK pour {coach_username}: CM={metrics.get('cm')}, Ratio={metrics.get('ratioMktg')}%, Taux={metrics.get('tauxVente')}%")
        return True

    except Exception as e:
        print(f"[COACH METRICS] ERREUR sauvegarde {coach_username}: {e}")
        return False


# ========== GESTION DES OBJECTIFS MENSUELS PAR ENTREPRENEUR ==========

def get_coach_objectifs_mensuels_file(coach_username):
    """
    Retourne le chemin du fichier JSON des objectifs mensuels pour un coach
    """
    return DATA_DIR / f"{coach_username}_objectifs_mensuels.json"


def load_coach_objectifs_mensuels(coach_username):
    """
    Charge les objectifs mensuels par entrepreneur pour un coach

    Args:
        coach_username: Nom d'utilisateur du coach

    Returns:
        dict: Dictionnaire {
            "2026-01": {
                "entrepreneur1": 100,
                "entrepreneur2": 120
            },
            "2026-02": {...}
        }
    """
    file_path = get_coach_objectifs_mensuels_file(coach_username)

    if not file_path.exists():
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('objectifs', {})
    except Exception as e:
        print(f"[COACH OBJECTIFS MENSUELS] Erreur lecture {coach_username}: {e}")
        return {}


def save_coach_objectifs_mensuels(coach_username, objectifs):
    """
    Sauvegarde les objectifs mensuels par entrepreneur pour un coach

    Args:
        coach_username: Nom d'utilisateur du coach
        objectifs: Dictionnaire {
            "2026-01": {
                "entrepreneur1": 100,
                "entrepreneur2": 120
            },
            "2026-02": {...}
        }

    Returns:
        bool: True si succès, False sinon
    """
    file_path = get_coach_objectifs_mensuels_file(coach_username)

    try:
        data = {
            'coach_username': coach_username,
            'objectifs': objectifs,
            'last_updated': datetime.now().isoformat()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[COACH OBJECTIFS MENSUELS] Sauvegarde OK pour {coach_username}: {len(objectifs)} mois")
        return True

    except Exception as e:
        print(f"[COACH OBJECTIFS MENSUELS] ERREUR sauvegarde {coach_username}: {e}")
        return False


def get_entrepreneur_objectif_for_month(coach_username, entrepreneur_username, month_key):
    """
    Récupère l'objectif d'un entrepreneur pour un mois donné

    Args:
        coach_username: Nom d'utilisateur du coach
        entrepreneur_username: Nom d'utilisateur de l'entrepreneur
        month_key: Clé du mois au format "2026-01"

    Returns:
        float: Valeur de l'objectif (0 si non défini)
    """
    objectifs = load_coach_objectifs_mensuels(coach_username)

    if month_key not in objectifs:
        return 0

    month_objectifs = objectifs[month_key]
    return float(month_objectifs.get(entrepreneur_username, 0))
