"""
Coach Team Objectifs - Gestion des prévisions d'objectifs par coach
"""

import os
import json
from datetime import datetime
from pathlib import Path

# Chemin de base pour les données
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "coach_previsions"
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

        print(f"[COACH PREVISIONS] ✅ Sauvegardé pour {coach_username}: {len(previsions)} prévisions")
        return True

    except Exception as e:
        print(f"[COACH PREVISIONS] ❌ Erreur sauvegarde {coach_username}: {e}")
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
