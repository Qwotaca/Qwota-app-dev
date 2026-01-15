"""
Coach Team Objectifs - Gestion des prévisions d'objectifs par coach
UTILISE UNIQUEMENT LE FICHIER RPO JSON
"""

from QE.Backend.rpo import load_user_rpo_data, save_user_rpo_data


# ========== GESTION DES MÉTRIQUES COACH (CM, RATIO MARKETING, TAUX DE VENTE) ==========

def load_coach_metrics(coach_username):
    """
    Charge les métriques prévisionnelles d'un coach depuis le RPO JSON

    Args:
        coach_username: Nom d'utilisateur du coach

    Returns:
        dict: Dictionnaire {cm: X, ratioMktg: Y, tauxVente: Z}
    """
    try:
        rpo_data = load_user_rpo_data(coach_username)
        coach_previsions = rpo_data.get('coach_previsions', {})
        return {
            'cm': coach_previsions.get('cm', 0),
            'ratioMktg': coach_previsions.get('ratioMktg', 0),
            'tauxVente': coach_previsions.get('tauxVente', 0)
        }
    except Exception as e:
        print(f"[COACH METRICS] Erreur lecture {coach_username}: {e}")
        return {'cm': 0, 'ratioMktg': 0, 'tauxVente': 0}


def save_coach_metrics(coach_username, metrics):
    """
    Sauvegarde les métriques prévisionnelles d'un coach dans le RPO JSON

    Args:
        coach_username: Nom d'utilisateur du coach
        metrics: Dictionnaire {cm: X, ratioMktg: Y, tauxVente: Z}

    Returns:
        bool: True si succès, False sinon
    """
    try:
        rpo_data = load_user_rpo_data(coach_username)

        if 'coach_previsions' not in rpo_data:
            rpo_data['coach_previsions'] = {}

        rpo_data['coach_previsions']['cm'] = metrics.get('cm', 0)
        rpo_data['coach_previsions']['ratioMktg'] = metrics.get('ratioMktg', 0)
        rpo_data['coach_previsions']['tauxVente'] = metrics.get('tauxVente', 0)

        save_user_rpo_data(coach_username, rpo_data)

        print(f"[COACH METRICS] Sauvegarde OK pour {coach_username}: CM={metrics.get('cm')}, Ratio={metrics.get('ratioMktg')}, Taux={metrics.get('tauxVente')}")
        return True

    except Exception as e:
        print(f"[COACH METRICS] ERREUR sauvegarde {coach_username}: {e}")
        return False


# ========== GESTION DES PRÉVISIONS D'OBJECTIFS ==========

def load_coach_previsions(coach_username):
    """
    Charge les prévisions d'objectifs d'un coach (entrepreneurs_metrics)

    Args:
        coach_username: Nom d'utilisateur du coach

    Returns:
        dict: Dictionnaire {entrepreneur_username: objectif_ca}
    """
    try:
        rpo_data = load_user_rpo_data(coach_username)
        entrepreneurs_metrics = rpo_data.get('entrepreneurs_metrics', {})

        # Retourner les objectif_ca de chaque entrepreneur
        previsions = {}
        for ent_username, metrics in entrepreneurs_metrics.items():
            previsions[ent_username] = metrics.get('objectif_ca', 0)

        return previsions
    except Exception as e:
        print(f"[COACH PREVISIONS] Erreur lecture {coach_username}: {e}")
        return {}


def save_coach_previsions(coach_username, previsions):
    """
    Sauvegarde les prévisions d'objectifs dans entrepreneurs_metrics

    Args:
        coach_username: Nom d'utilisateur du coach
        previsions: Dictionnaire {entrepreneur_username: objectif_ca}

    Returns:
        bool: True si succès, False sinon
    """
    try:
        rpo_data = load_user_rpo_data(coach_username)

        if 'entrepreneurs_metrics' not in rpo_data:
            rpo_data['entrepreneurs_metrics'] = {}

        # Mettre à jour les objectif_ca
        for ent_username, objectif in previsions.items():
            if ent_username not in rpo_data['entrepreneurs_metrics']:
                rpo_data['entrepreneurs_metrics'][ent_username] = {
                    'objectif_ca': objectif,
                    'cm': 2500,
                    'ratioMktg': 85,
                    'tauxVente': 30
                }
            else:
                rpo_data['entrepreneurs_metrics'][ent_username]['objectif_ca'] = objectif

        # Mettre à jour totalObjectif dans coach_previsions
        if 'coach_previsions' not in rpo_data:
            rpo_data['coach_previsions'] = {}

        total = sum(float(v) for v in previsions.values())
        rpo_data['coach_previsions']['totalObjectif'] = total

        save_user_rpo_data(coach_username, rpo_data)

        print(f"[COACH PREVISIONS] Sauvegarde OK pour {coach_username}: {len(previsions)} previsions, total={total}")
        return True

    except Exception as e:
        print(f"[COACH PREVISIONS] ERREUR sauvegarde {coach_username}: {e}")
        return False


def get_team_objectif_total(coach_username):
    """
    Récupère le total des objectifs de l'équipe depuis coach_previsions

    Args:
        coach_username: Nom d'utilisateur du coach

    Returns:
        float: Total des prévisions
    """
    try:
        rpo_data = load_user_rpo_data(coach_username)
        return rpo_data.get('coach_previsions', {}).get('totalObjectif', 0)
    except Exception as e:
        print(f"[COACH PREVISIONS] Erreur lecture total {coach_username}: {e}")
        return 0


# ========== GESTION DES MÉTRIQUES PAR ENTREPRENEUR ==========

def load_entrepreneur_metrics(coach_username, entrepreneur_username):
    """
    Charge les métriques d'un entrepreneur spécifique

    Args:
        coach_username: Nom d'utilisateur du coach
        entrepreneur_username: Nom d'utilisateur de l'entrepreneur

    Returns:
        dict: {objectif_ca, cm, ratioMktg, tauxVente}
    """
    try:
        rpo_data = load_user_rpo_data(coach_username)
        entrepreneurs_metrics = rpo_data.get('entrepreneurs_metrics', {})
        return entrepreneurs_metrics.get(entrepreneur_username, {
            'objectif_ca': 0,
            'cm': 2500,
            'ratioMktg': 85,
            'tauxVente': 30
        })
    except Exception as e:
        print(f"[COACH] Erreur lecture metrics {entrepreneur_username}: {e}")
        return {'objectif_ca': 0, 'cm': 2500, 'ratioMktg': 85, 'tauxVente': 30}


def save_entrepreneur_metrics(coach_username, entrepreneur_username, metrics):
    """
    Sauvegarde les métriques d'un entrepreneur spécifique

    Args:
        coach_username: Nom d'utilisateur du coach
        entrepreneur_username: Nom d'utilisateur de l'entrepreneur
        metrics: {objectif_ca, cm, ratioMktg, tauxVente}

    Returns:
        bool: True si succès, False sinon
    """
    try:
        rpo_data = load_user_rpo_data(coach_username)

        if 'entrepreneurs_metrics' not in rpo_data:
            rpo_data['entrepreneurs_metrics'] = {}

        rpo_data['entrepreneurs_metrics'][entrepreneur_username] = metrics

        # Recalculer totalObjectif
        if 'coach_previsions' not in rpo_data:
            rpo_data['coach_previsions'] = {}

        total = sum(
            ent.get('objectif_ca', 0)
            for ent in rpo_data['entrepreneurs_metrics'].values()
        )
        rpo_data['coach_previsions']['totalObjectif'] = total

        save_user_rpo_data(coach_username, rpo_data)

        print(f"[COACH] Sauvegarde metrics {entrepreneur_username} OK")
        return True

    except Exception as e:
        print(f"[COACH] ERREUR sauvegarde metrics {entrepreneur_username}: {e}")
        return False
