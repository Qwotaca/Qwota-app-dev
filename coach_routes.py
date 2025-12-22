"""
Routes Flask pour la gestion des prévisions d'objectifs de l'équipe du coach
"""

from flask import Blueprint, request, jsonify
from QE.Backend.coach_previsions import (
    load_coach_previsions,
    save_coach_previsions,
    get_team_objectif_total
)

coach_bp = Blueprint('coach', __name__)


@coach_bp.route('/api/coach/team-objectifs', methods=['GET'])
def get_team_objectifs():
    """
    Récupère les prévisions d'objectifs pour l'équipe d'un coach

    Query params:
        coach_username: Nom d'utilisateur du coach

    Returns:
        {
            "success": True,
            "previsions": {
                "entrepreneur1": 100000,
                "entrepreneur2": 150000
            },
            "total": 250000
        }
    """
    try:
        coach_username = request.args.get('coach_username')

        if not coach_username:
            return jsonify({
                'success': False,
                'error': 'coach_username manquant'
            }), 400

        previsions = load_coach_previsions(coach_username)
        total = get_team_objectif_total(coach_username)

        return jsonify({
            'success': True,
            'previsions': previsions,
            'total': total
        })

    except Exception as e:
        print(f"[COACH API] Erreur GET team-objectifs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@coach_bp.route('/api/coach/team-objectifs', methods=['POST'])
def save_team_objectifs():
    """
    Sauvegarde les prévisions d'objectifs pour l'équipe d'un coach

    Body JSON:
        {
            "coach_username": "coach1",
            "previsions": {
                "entrepreneur1": 100000,
                "entrepreneur2": 150000
            }
        }

    Returns:
        {
            "success": True,
            "total": 250000
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        coach_username = data.get('coach_username')
        previsions = data.get('previsions', {})

        if not coach_username:
            return jsonify({
                'success': False,
                'error': 'coach_username manquant'
            }), 400

        # Sauvegarder les prévisions
        success = save_coach_previsions(coach_username, previsions)

        if success:
            total = get_team_objectif_total(coach_username)
            return jsonify({
                'success': True,
                'total': total
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erreur lors de la sauvegarde'
            }), 500

    except Exception as e:
        print(f"[COACH API] Erreur POST team-objectifs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Export du blueprint pour l'import dans l'app principale
__all__ = ['coach_bp']
