"""
Direction Team Objectifs - Gestion des prévisions d'objectifs par direction pour les coaches
UTILISE UNIQUEMENT LE FICHIER RPO JSON (direction_rpo.json)
"""

from QE.Backend.rpo import load_user_rpo_data, save_user_rpo_data

# Tous les users direction partagent le meme fichier: direction_rpo.json
DIRECTION_USERNAME = "direction"


# ========== GESTION DES MÉTRIQUES DIRECTION (CM, RATIO MARKETING, TAUX DE VENTE) ==========

def load_direction_metrics(direction_username):
    """
    Charge les métriques d'équipe de la direction depuis le RPO JSON

    Args:
        direction_username: Ignoré - tous les comptes direction partagent le même fichier

    Returns:
        dict: Dictionnaire {cm: X, ratioMktg: Y, tauxVente: Z}
    """
    try:
        rpo_data = load_user_rpo_data(DIRECTION_USERNAME)
        direction_previsions = rpo_data.get('direction_previsions', {})
        return {
            'cm': direction_previsions.get('cm', 0),
            'ratioMktg': direction_previsions.get('ratioMktg', 0),
            'tauxVente': direction_previsions.get('tauxVente', 0)
        }
    except Exception as e:
        print(f"[DIRECTION METRICS] Erreur lecture: {e}")
        return {'cm': 0, 'ratioMktg': 0, 'tauxVente': 0}


def save_direction_metrics(direction_username, metrics):
    """
    Sauvegarde les métriques d'équipe de la direction dans le RPO JSON

    Args:
        direction_username: Ignoré - tous les comptes direction partagent le même fichier
        metrics: Dictionnaire {cm: X, ratioMktg: Y, tauxVente: Z}

    Returns:
        bool: True si succès, False sinon
    """
    try:
        rpo_data = load_user_rpo_data(DIRECTION_USERNAME)

        if 'direction_previsions' not in rpo_data:
            rpo_data['direction_previsions'] = {}

        rpo_data['direction_previsions']['cm'] = metrics.get('cm', 0)
        rpo_data['direction_previsions']['ratioMktg'] = metrics.get('ratioMktg', 0)
        rpo_data['direction_previsions']['tauxVente'] = metrics.get('tauxVente', 0)

        save_user_rpo_data(DIRECTION_USERNAME, rpo_data)

        print(f"[DIRECTION METRICS] Sauvegarde OK: CM={metrics.get('cm')}, Ratio={metrics.get('ratioMktg')}, Taux={metrics.get('tauxVente')}")
        return True

    except Exception as e:
        print(f"[DIRECTION METRICS] ERREUR sauvegarde: {e}")
        return False


# ========== GESTION DES PRÉVISIONS D'OBJECTIFS PAR COACH ==========

def load_direction_previsions(direction_username):
    """
    Charge les prévisions d'objectifs par coach (coaches_metrics)

    Args:
        direction_username: Ignoré - tous les comptes direction partagent le même fichier

    Returns:
        dict: Dictionnaire {coach_username: totalObjectif}
    """
    try:
        rpo_data = load_user_rpo_data(DIRECTION_USERNAME)
        coaches_metrics = rpo_data.get('coaches_metrics', {})

        # Retourner les totalObjectif de chaque coach
        previsions = {}
        for coach_username, metrics in coaches_metrics.items():
            previsions[coach_username] = metrics.get('totalObjectif', 0)

        return previsions
    except Exception as e:
        print(f"[DIRECTION PREVISIONS] Erreur lecture: {e}")
        return {}


def save_direction_previsions(direction_username, previsions):
    """
    Sauvegarde les prévisions d'objectifs par coach dans coaches_metrics

    Args:
        direction_username: Ignoré - tous les comptes direction partagent le même fichier
        previsions: Dictionnaire {coach_username: totalObjectif}

    Returns:
        bool: True si succès, False sinon
    """
    try:
        rpo_data = load_user_rpo_data(DIRECTION_USERNAME)

        if 'coaches_metrics' not in rpo_data:
            rpo_data['coaches_metrics'] = {}

        # Mettre à jour les totalObjectif
        for coach_username, objectif in previsions.items():
            if coach_username not in rpo_data['coaches_metrics']:
                rpo_data['coaches_metrics'][coach_username] = {
                    'totalObjectif': objectif,
                    'cm': 2500,
                    'ratioMktg': 85,
                    'tauxVente': 30
                }
            else:
                rpo_data['coaches_metrics'][coach_username]['totalObjectif'] = objectif

        # Mettre à jour totalObjectif global dans direction_previsions
        if 'direction_previsions' not in rpo_data:
            rpo_data['direction_previsions'] = {}

        total = sum(float(v) for v in previsions.values())
        rpo_data['direction_previsions']['totalObjectif'] = total

        save_user_rpo_data(DIRECTION_USERNAME, rpo_data)

        print(f"[DIRECTION PREVISIONS] Sauvegarde OK: {len(previsions)} coaches, total={total}")
        return True

    except Exception as e:
        print(f"[DIRECTION PREVISIONS] ERREUR sauvegarde: {e}")
        return False


def get_direction_team_objectif_total(direction_username):
    """
    Récupère le total des objectifs de tous les coaches

    Args:
        direction_username: Ignoré - tous les comptes direction partagent le même fichier

    Returns:
        float: Total des prévisions
    """
    try:
        rpo_data = load_user_rpo_data(DIRECTION_USERNAME)
        return rpo_data.get('direction_previsions', {}).get('totalObjectif', 0)
    except Exception as e:
        print(f"[DIRECTION PREVISIONS] Erreur lecture total: {e}")
        return 0


# ========== GESTION DES MÉTRIQUES PAR COACH ==========

def load_coach_metrics_from_direction(direction_username, coach_username):
    """
    Charge les métriques d'un coach spécifique depuis le fichier direction

    Args:
        direction_username: Ignoré
        coach_username: Nom d'utilisateur du coach

    Returns:
        dict: {totalObjectif, cm, ratioMktg, tauxVente}
    """
    try:
        rpo_data = load_user_rpo_data(DIRECTION_USERNAME)
        coaches_metrics = rpo_data.get('coaches_metrics', {})
        return coaches_metrics.get(coach_username, {
            'totalObjectif': 0,
            'cm': 2500,
            'ratioMktg': 85,
            'tauxVente': 30
        })
    except Exception as e:
        print(f"[DIRECTION] Erreur lecture metrics {coach_username}: {e}")
        return {'totalObjectif': 0, 'cm': 2500, 'ratioMktg': 85, 'tauxVente': 30}


def save_coach_metrics_from_direction(direction_username, coach_username, metrics):
    """
    Sauvegarde les métriques d'un coach spécifique dans le fichier direction

    Args:
        direction_username: Ignoré
        coach_username: Nom d'utilisateur du coach
        metrics: {totalObjectif, cm, ratioMktg, tauxVente}

    Returns:
        bool: True si succès, False sinon
    """
    try:
        rpo_data = load_user_rpo_data(DIRECTION_USERNAME)

        if 'coaches_metrics' not in rpo_data:
            rpo_data['coaches_metrics'] = {}

        rpo_data['coaches_metrics'][coach_username] = metrics

        # Recalculer totalObjectif global
        if 'direction_previsions' not in rpo_data:
            rpo_data['direction_previsions'] = {}

        total = sum(
            coach.get('totalObjectif', 0)
            for coach in rpo_data['coaches_metrics'].values()
        )
        rpo_data['direction_previsions']['totalObjectif'] = total

        save_user_rpo_data(DIRECTION_USERNAME, rpo_data)

        print(f"[DIRECTION] Sauvegarde metrics {coach_username} OK")
        return True

    except Exception as e:
        print(f"[DIRECTION] ERREUR sauvegarde metrics {coach_username}: {e}")
        return False
