"""
Backend routes pour RPO (Résultats, Prévisions, Objectifs)
Gère les données annuelles, mensuelles et hebdomadaires par utilisateur
"""

import json
import os
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Locks pour éviter les synchronisations simultanées
_coach_sync_locks = {}  # Dict[coach_username, Lock]
_direction_sync_lock = threading.Lock()
_locks_lock = threading.Lock()  # Lock pour accéder au dict des locks

# Fuseau horaire de Toronto
TORONTO_TZ = ZoneInfo("America/Toronto")

def get_toronto_now():
    """Retourne l'heure actuelle à Toronto"""
    return datetime.now(TORONTO_TZ)

def parse_date_toronto(date_str: str) -> datetime:
    """Parse une date et la convertit au fuseau horaire de Toronto"""
    try:
        # Parse la date (format: YYYY-MM-DD, ISO, ou DD/MM/YYYY)
        if 'T' in date_str:
            # Format ISO avec éventuellement un timezone
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=TORONTO_TZ)
            else:
                dt = dt.astimezone(TORONTO_TZ)
        elif '/' in date_str:
            # Format DD/MM/YYYY (ex: 09/10/2025)
            dt = datetime.strptime(date_str, '%d/%m/%Y')
            dt = dt.replace(tzinfo=TORONTO_TZ)
        else:
            # Format YYYY-MM-DD
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            dt = dt.replace(tzinfo=TORONTO_TZ)
        return dt
    except Exception as e:
        print(f"Erreur parsing date {date_str}: {e}")
        return get_toronto_now()

# Dossier de stockage des données RPO
# Utiliser le même dossier que les autres données de l'application
import sys
if sys.platform == 'win32':
    # Windows - remonter à la racine du projet (3 niveaux depuis QE/Backend/rpo.py)
    RPO_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'rpo')
else:
    # Unix/Linux (Production sur Render)
    # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
    RPO_DATA_DIR = os.path.join(base_cloud, "rpo")

os.makedirs(RPO_DATA_DIR, exist_ok=True)


def get_user_rpo_file(username: str) -> str:
    """Retourne le chemin du fichier RPO pour un utilisateur"""
    return os.path.join(RPO_DATA_DIR, f"{username}_rpo.json")


def load_user_rpo_data(username: str) -> Dict[str, Any]:
    """
    Charge les données RPO d'un utilisateur
    Retourne la structure complète avec annual, monthly, weekly
    """
    filepath = get_user_rpo_file(username)

    if not os.path.exists(filepath):
        # Structure par défaut
        return {
            "annual": {
                "objectif_ca": 0,
                "objectif_pap": 0,
                "objectif_rep": 0,
                "hr_pap_reel": 0,
                "estimation_reel": 0,
                "contract_reel": 0,
                "dollar_reel": 0,
                "hrpap_vise": 0,
                "estimation_vise": 0,
                "contract_vise": 0,
                "dollar_vise": 0,
                "mktg_vise": 0,
                "vente_vise": 0,
                "moyen_vise": 0,
                "tendance_vise": 0,
                "ratio_mktg": 85,
                "cm_prevision": 2500,
                "taux_vente": 30,
                "mktg_reel": 0,
                "vente_reel": 0,
                "moyen_reel": 0,
                "prod_horaire": 0
            },
            "monthly": {
                # dec2025 (décembre 2025), jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec
                month: {
                    "obj_pap": 0,
                    "obj_rep": 0,
                    "hrpap_vise": 0,
                    "estimation_vise": 0,
                    "contract_vise": 0,
                    "dollar_vise": 0,
                    "hrpap_reel": 0,
                    "estimation_reel": 0,
                    "contract_reel": 0,
                    "dollar_reel": 0
                }
                for month in ['dec2025', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            },
            "weekly": {
                # Structure: {monthIndex: {weekNumber: {data}}}
                str(month_idx): {
                    str(week_num): {
                        "h_marketing": "-",
                        "estimation": 0,
                        "contract": 0,
                        "dollar": 0,
                        "commentaire": "Problème: - | Focus: -",
                        "rating": 0
                    }
                    for week_num in range(1, 6)
                }
                for month_idx in [-2] + list(range(12))
            }
        }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement RPO pour {username}: {e}")
        # Retourne structure par défaut en cas d'erreur
        return {
            "annual": {
                "objectif_ca": 0,
                "objectif_pap": 0,
                "objectif_rep": 0,
                "hr_pap_reel": 0,
                "estimation_reel": 0,
                "contract_reel": 0,
                "dollar_reel": 0,
                "hrpap_vise": 0,
                "estimation_vise": 0,
                "contract_vise": 0,
                "dollar_vise": 0,
                "mktg_vise": 0,
                "vente_vise": 0,
                "moyen_vise": 0,
                "tendance_vise": 0,
                "ratio_mktg": 85,
                "cm_prevision": 2500,
                "taux_vente": 30,
                "mktg_reel": 0,
                "vente_reel": 0,
                "moyen_reel": 0,
                "prod_horaire": 0
            },
            "monthly": {
                month: {
                    "obj_pap": 0,
                    "obj_rep": 0,
                    "hrpap_vise": 0,
                    "estimation_vise": 0,
                    "contract_vise": 0,
                    "dollar_vise": 0,
                    "hrpap_reel": 0,
                    "estimation_reel": 0,
                    "contract_reel": 0,
                    "dollar_reel": 0
                }
                for month in ['dec2025', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            },
            "weekly": {
                str(month_idx): {
                    str(week_num): {
                        "h_marketing": "-",
                        "estimation": 0,
                        "contract": 0,
                        "dollar": 0,
                        "commentaire": "Problème: - | Focus: -",
                        "rating": 0
                    }
                    for week_num in range(1, 6)
                }
                for month_idx in [-2] + list(range(12))
            }
        }


def save_user_rpo_data(username: str, data: Dict[str, Any]) -> bool:
    """
    Sauvegarde les données RPO d'un utilisateur
    """
    filepath = get_user_rpo_file(username)
    print(f"[DEBUG] [SAVE RPO] Attempting to save for user: {username}", flush=True)
    print(f"[DEBUG] [SAVE RPO] Target filepath: {filepath}", flush=True)
    print(f"[DEBUG] [SAVE RPO] RPO_DATA_DIR: {RPO_DATA_DIR}", flush=True)
    print(f"[DEBUG] [SAVE RPO] Directory exists? {os.path.exists(os.path.dirname(filepath))}", flush=True)
    print(f"[DEBUG] [SAVE RPO] File exists before save? {os.path.exists(filepath)}", flush=True)

    try:
        # Ajouter timestamp de dernière modification (heure de Toronto)
        data['last_updated'] = get_toronto_now().isoformat()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[DEBUG] [SAVE RPO] File written successfully!", flush=True)
        print(f"[DEBUG] [SAVE RPO] File exists after save? {os.path.exists(filepath)}", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] [SAVE RPO] Failed to save RPO for {username}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False


def update_annual_data(username: str, annual_data: Dict[str, Any]) -> bool:
    """
    Met à jour les données annuelles
    """
    rpo_data = load_user_rpo_data(username)
    rpo_data['annual'] = annual_data
    return save_user_rpo_data(username, rpo_data)


def update_monthly_data(username: str, month: str, monthly_data: Dict[str, Any]) -> bool:
    """
    Met à jour les données d'un mois spécifique
    month: 'jan', 'feb', 'mar', etc.
    """
    rpo_data = load_user_rpo_data(username)

    if 'monthly' not in rpo_data:
        rpo_data['monthly'] = {}

    rpo_data['monthly'][month] = monthly_data
    return save_user_rpo_data(username, rpo_data)


def update_weekly_data(username: str, month_index: int, week_number: int, weekly_data: Dict[str, Any]) -> bool:
    """
    Met à jour les données d'une semaine spécifique
    month_index: 0-11 (janvier=0, décembre=11)
    week_number: numéro de la semaine dans le mois
    """
    print(f"[BACKEND-SAVE] 📥 Réception des données pour {username}, mois {month_index}, semaine {week_number}", flush=True)
    print(f"[BACKEND-SAVE] 📊 Données reçues: {weekly_data}", flush=True)
    if 'prod_horaire' in weekly_data:
        print(f"[BACKEND-SAVE] 💰 Prod Horaire: {weekly_data['prod_horaire']}$/h", flush=True)

    rpo_data = load_user_rpo_data(username)

    if 'weekly' not in rpo_data:
        rpo_data['weekly'] = {}

    month_key = str(month_index)
    if month_key not in rpo_data['weekly']:
        rpo_data['weekly'][month_key] = {}

    week_key = str(week_number)

    # MERGE au lieu d'écraser: si des données existent déjà, on les garde et on update seulement les nouveaux champs
    if week_key in rpo_data['weekly'][month_key]:
        print(f"[BACKEND-SAVE] 🔄 Merge avec données existantes pour semaine {week_number}", flush=True)
        existing_data = rpo_data['weekly'][month_key][week_key]
        # Merger les nouvelles données avec les anciennes (les nouvelles ont priorité)
        existing_data.update(weekly_data)
        rpo_data['weekly'][month_key][week_key] = existing_data
    else:
        print(f"[BACKEND-SAVE] 🆕 Création nouvelle semaine {week_number}", flush=True)
        rpo_data['weekly'][month_key][week_key] = weekly_data

    result = save_user_rpo_data(username, rpo_data)
    if result:
        print(f"[BACKEND-SAVE] ✅ Données sauvegardées avec succès")

        # Synchroniser le RPO du coach si cet entrepreneur est assigné à un coach
        try:
            from QE.Backend.coach_access import get_coach_for_entrepreneur
            coach_username = get_coach_for_entrepreneur(username)
            if coach_username:
                print(f"[BACKEND-SAVE] Synchronisation RPO du coach {coach_username}...", flush=True)
                sync_coach_rpo(coach_username)
        except Exception as coach_sync_error:
            print(f"[WARN] [BACKEND-SAVE] Erreur synchronisation RPO coach: {coach_sync_error}", flush=True)
    else:
        print(f"[BACKEND-SAVE] ❌ Échec de la sauvegarde")

    return result


def get_annual_data(username: str) -> Dict[str, Any]:
    """Récupère les données annuelles"""
    rpo_data = load_user_rpo_data(username)
    return rpo_data.get('annual', {})


def get_monthly_data(username: str, month: str) -> Dict[str, Any]:
    """Récupère les données d'un mois"""
    rpo_data = load_user_rpo_data(username)
    return rpo_data.get('monthly', {}).get(month, {})


def get_all_monthly_data(username: str) -> Dict[str, Any]:
    """Récupère toutes les données mensuelles"""
    rpo_data = load_user_rpo_data(username)
    return rpo_data.get('monthly', {})


def get_weekly_data(username: str, month_index: int, week_number: int) -> Dict[str, Any]:
    """Récupère les données d'une semaine spécifique"""
    rpo_data = load_user_rpo_data(username)
    month_key = str(month_index)
    week_key = str(week_number)
    return rpo_data.get('weekly', {}).get(month_key, {}).get(week_key, {})


def get_all_weekly_data_for_month(username: str, month_index: int) -> Dict[str, Any]:
    """Récupère toutes les données hebdomadaires d'un mois"""
    rpo_data = load_user_rpo_data(username)
    month_key = str(month_index)
    return rpo_data.get('weekly', {}).get(month_key, {})


def get_week_number_from_date(date_str: str) -> tuple:
    """
    Retourne (month_index, week_number) basé sur la date (en heure de Toronto)
    month_index: -2 (octobre 2025), 0-8 (janvier-septembre 2026)
    week_number: 1-5 (semaine dans le mois, basée sur les lundis)

    Pour Octobre 2025:
    - Semaine 1: 6-12 oct (lundi-dimanche)
    - Semaine 2: 13-19 oct
    - Semaine 3: 20-26 oct
    - Semaine 4: 27 oct - 2 nov

    Pour 2026: Les semaines commencent le lundi
    """
    from datetime import timedelta

    try:
        # Parse la date avec le fuseau horaire de Toronto
        date = parse_date_toronto(date_str)

        # Déterminer month_index selon l'année et le mois
        if date.year == 2025 and date.month == 12:
            month_index = -2  # Décembre 2025 (premier mois du cycle fiscal)

            # Pour décembre 2025: trouver le premier lundi et calculer les semaines
            first_day = datetime(date.year, date.month, 1, tzinfo=TORONTO_TZ)
            if first_day.weekday() == 0:  # Si le 1er est déjà un lundi
                first_monday = first_day
            else:
                days_until_monday = (7 - first_day.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                first_monday = first_day + timedelta(days=days_until_monday)

            # Compter les lundis depuis le début du mois jusqu'à cette date
            if date < first_monday:
                week_number = 1  # Avant le premier lundi = semaine 1
            else:
                days_since_first_monday = (date - first_monday).days
                week_number = (days_since_first_monday // 7) + 1

        elif date.year == 2026 and 1 <= date.month <= 12:  # Janvier-Décembre 2026
            # NOUVELLE LOGIQUE: Une semaine appartient au mois où elle COMMENCE (lundi)
            # Trouver le lundi de la semaine qui contient cette date
            days_since_monday = date.weekday()  # 0=Monday, 6=Sunday
            monday_of_week = date - timedelta(days=days_since_monday)

            # CAS SPÉCIAL: Janvier 1-4 2026 (avant le 5 janvier qui est un lundi)
            if date.month == 1 and date.day < 5:
                print(f"[DEBUG] Date {date_str} est avant le 5 janvier -> Décembre semaine 5")
                return (-2, 5)  # Décembre 2025, semaine 5

            # Le mois auquel appartient cette semaine est le mois du LUNDI
            week_belongs_to_month = monday_of_week.month
            week_belongs_to_year = monday_of_week.year

            # Si le lundi est dans un autre mois, rediriger vers ce mois
            if week_belongs_to_month != date.month or week_belongs_to_year != date.year:
                # Cette date appartient à la semaine d'un autre mois
                # Appeler récursivement avec la date du lundi
                print(f"[DEBUG] Date {date_str} appartient à la semaine du {monday_of_week.strftime('%Y-%m-%d')}")
                return get_week_number_from_date(monday_of_week.strftime('%Y-%m-%d'))

            # Trouver le premier lundi du mois du lundi de la semaine
            first_day = datetime(week_belongs_to_year, week_belongs_to_month, 1, tzinfo=TORONTO_TZ)
            if first_day.weekday() == 0:  # Si le 1er est déjà un lundi
                first_monday = first_day
            else:
                days_until_monday = 7 - first_day.weekday()
                first_monday = first_day + timedelta(days=days_until_monday)

            month_index = week_belongs_to_month - 1  # 0-11 pour janvier-décembre 2026

            # Compter les lundis depuis le début du mois jusqu'au lundi de cette semaine
            days_since_first_monday = (monday_of_week - first_monday).days
            week_number = (days_since_first_monday // 7) + 1

        else:
            # Default: dates hors période fiscale (décembre 2025 - décembre 2026)
            month_index = 0  # Default janvier 2026
            week_number = 1

        return (month_index, week_number)
    except Exception as e:
        print(f"Erreur parsing date {date_str}: {e}")
        return (0, 1)  # Default janvier 2026 semaine 1


def sync_direction_rpo() -> bool:
    """
    Synchronise le RPO direction en agrégeant les données de tous les coaches
    Agrège: h_marketing, estimation, contract, dollar, produit
    Utilise un lock pour éviter les synchronisations simultanées
    """
    # Acquérir le lock pour direction
    with _direction_sync_lock:
        try:
            import sqlite3
            from database import get_database_path

            # Récupérer tous les coaches actifs
            DB_PATH = get_database_path()
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username FROM users WHERE role='coach' AND is_active=1")
                coaches = [row[0] for row in cursor.fetchall()]

            if not coaches:
                print(f"[DIRECTION RPO] Aucun coach actif trouvé", flush=True)
                return False

            print(f"[DIRECTION RPO] Agrégation de {len(coaches)} coaches: {coaches}", flush=True)

            # Charger le RPO direction (ou créer structure vide)
            direction_rpo = load_user_rpo_data('direction')

            # Réinitialiser les données weekly de direction
            if 'weekly' not in direction_rpo:
                direction_rpo['weekly'] = {}

            # Initialiser toutes les semaines à 0
            all_months = [-2] + list(range(12))
            for month_idx in all_months:
                month_key = str(month_idx)
                if month_key not in direction_rpo['weekly']:
                    direction_rpo['weekly'][month_key] = {}

                for week_number in range(1, 6):
                    week_key = str(week_number)
                    if week_key not in direction_rpo['weekly'][month_key]:
                        direction_rpo['weekly'][month_key][week_key] = {}

                    # Réinitialiser TOUS les champs agrégés à 0
                    direction_rpo['weekly'][month_key][week_key]['h_marketing'] = 0
                    direction_rpo['weekly'][month_key][week_key]['estimation'] = 0
                    direction_rpo['weekly'][month_key][week_key]['contract'] = 0
                    direction_rpo['weekly'][month_key][week_key]['dollar'] = 0
                    direction_rpo['weekly'][month_key][week_key]['produit'] = 0

            # Agréger les données de tous les coaches
            for coach_username in coaches:
                coach_rpo = load_user_rpo_data(coach_username)

                if 'weekly' not in coach_rpo:
                    continue

                # Parcourir tous les mois et semaines du coach
                for month_key, weeks_data in coach_rpo['weekly'].items():
                    if month_key not in direction_rpo['weekly']:
                        direction_rpo['weekly'][month_key] = {}

                    for week_key, week_data in weeks_data.items():
                        if week_key not in direction_rpo['weekly'][month_key]:
                            direction_rpo['weekly'][month_key][week_key] = {}

                        # Agréger h_marketing (ignorer les "-" et valeurs non numériques)
                        h_marketing = week_data.get('h_marketing', '-')
                        if h_marketing not in ['-', '', None]:
                            try:
                                h_value = float(h_marketing)
                                current = direction_rpo['weekly'][month_key][week_key].get('h_marketing', 0)
                                if current == '-' or current is None:
                                    current = 0
                                direction_rpo['weekly'][month_key][week_key]['h_marketing'] = float(current) + h_value
                            except (ValueError, TypeError):
                                pass

                        # Agréger estimation, contract, dollar, produit (valeurs numériques)
                        for field in ['estimation', 'contract', 'dollar', 'produit']:
                            value = week_data.get(field, 0)
                            if value and value != 0:
                                try:
                                    numeric_value = float(value)
                                    current = direction_rpo['weekly'][month_key][week_key].get(field, 0)
                                    direction_rpo['weekly'][month_key][week_key][field] = float(current) + numeric_value
                                except (ValueError, TypeError):
                                    pass

            # Sauvegarder le RPO direction (APRÈS avoir agrégé tous les coaches)
            save_user_rpo_data('direction', direction_rpo)
            print(f"[DIRECTION RPO] Donnees agregees pour direction ({len(coaches)} coaches)", flush=True)
            return True

        except Exception as e:
            print(f"[ERREUR] [DIRECTION RPO] Erreur sync direction: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False


def sync_coach_rpo(coach_username: str) -> bool:
    """
    Synchronise le RPO d'un coach en agrégeant les données de tous ses entrepreneurs
    Agrège: h_marketing, estimation, contract, dollar, produit
    Utilise un lock par coach pour éviter les synchronisations simultanées
    """
    # Obtenir ou créer le lock pour ce coach
    with _locks_lock:
        if coach_username not in _coach_sync_locks:
            _coach_sync_locks[coach_username] = threading.Lock()
        coach_lock = _coach_sync_locks[coach_username]

    # Acquérir le lock pour ce coach
    with coach_lock:
        try:
            from QE.Backend.coach_access import get_entrepreneurs_for_coach

            # Récupérer tous les entrepreneurs du coach
            entrepreneurs = get_entrepreneurs_for_coach(coach_username)
            if not entrepreneurs:
                return False

            entrepreneur_usernames = [e['username'] for e in entrepreneurs]

            # Charger le RPO du coach (ou créer structure vide)
            coach_rpo = load_user_rpo_data(coach_username)

            # Réinitialiser les données weekly du coach
            if 'weekly' not in coach_rpo:
                coach_rpo['weekly'] = {}

            # Initialiser toutes les semaines avec h_marketing à 0
            all_months = [-2] + list(range(12))
            for month_idx in all_months:
                month_key = str(month_idx)
                if month_key not in coach_rpo['weekly']:
                    coach_rpo['weekly'][month_key] = {}

                for week_number in range(1, 6):
                    week_key = str(week_number)
                    if week_key not in coach_rpo['weekly'][month_key]:
                        coach_rpo['weekly'][month_key][week_key] = {}

                    # Réinitialiser TOUS les champs agrégés à 0
                    coach_rpo['weekly'][month_key][week_key]['h_marketing'] = 0
                    coach_rpo['weekly'][month_key][week_key]['estimation'] = 0
                    coach_rpo['weekly'][month_key][week_key]['contract'] = 0
                    coach_rpo['weekly'][month_key][week_key]['dollar'] = 0
                    coach_rpo['weekly'][month_key][week_key]['produit'] = 0

            # Agréger les h_marketing de tous les entrepreneurs
            for entrepreneur_username in entrepreneur_usernames:
                entrepreneur_rpo = load_user_rpo_data(entrepreneur_username)

                if 'weekly' not in entrepreneur_rpo:
                    continue

                # Parcourir tous les mois et semaines de l'entrepreneur
                for month_key, weeks_data in entrepreneur_rpo['weekly'].items():
                    if month_key not in coach_rpo['weekly']:
                        coach_rpo['weekly'][month_key] = {}

                    for week_key, week_data in weeks_data.items():
                        if week_key not in coach_rpo['weekly'][month_key]:
                            coach_rpo['weekly'][month_key][week_key] = {}

                        # Agréger h_marketing (ignorer les "-" et valeurs non numériques)
                        h_marketing = week_data.get('h_marketing', '-')
                        if h_marketing not in ['-', '', None]:
                            try:
                                h_value = float(h_marketing)
                                current = coach_rpo['weekly'][month_key][week_key].get('h_marketing', 0)
                                if current == '-' or current is None:
                                    current = 0
                                coach_rpo['weekly'][month_key][week_key]['h_marketing'] = float(current) + h_value
                            except (ValueError, TypeError):
                                pass

                        # Agréger estimation, contract, dollar, produit (valeurs numériques)
                        for field in ['estimation', 'contract', 'dollar', 'produit']:
                            value = week_data.get(field, 0)
                            if value and value != 0:
                                try:
                                    numeric_value = float(value)
                                    current = coach_rpo['weekly'][month_key][week_key].get(field, 0)
                                    coach_rpo['weekly'][month_key][week_key][field] = float(current) + numeric_value
                                except (ValueError, TypeError):
                                    pass

            # Sauvegarder le RPO du coach
            save_user_rpo_data(coach_username, coach_rpo)
            print(f"[COACH RPO] Donnees agregees chargees avec succes pour coach {coach_username} ({len(entrepreneur_usernames)} entrepreneurs)", flush=True)

            # Synchroniser le RPO direction après avoir mis à jour le coach
            try:
                sync_direction_rpo()
            except Exception as direction_sync_error:
                print(f"[WARN] [COACH RPO] Erreur synchronisation RPO direction: {direction_sync_error}", flush=True)

            return True

        except Exception as e:
            print(f"[ERREUR] [COACH RPO SYNC] Erreur sync coach {coach_username}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return False


def sync_soumissions_to_rpo(username: str) -> bool:
    """
    Synchronise les soumissions complètes et signées vers les données hebdomadaires RPO
    - Soumissions complètes -> Estimation réel
    - Soumissions signées -> Contrat réel + $ réel
    """
    import json
    import os

    print(f"[SYNC] [RPO SYNC] Debut synchronisation pour {username}", flush=True)

    try:
        # Charger les données RPO existantes
        rpo_data = load_user_rpo_data(username)

        # Réinitialiser les données hebdomadaires estimation/contract/dollar
        # Octobre 2025 (index -2) + 12 mois de 2026 (index 0-11)
        all_months = [-2] + list(range(12))

        for month_idx in all_months:
            month_key = str(month_idx)
            if month_key not in rpo_data['weekly']:
                rpo_data['weekly'][month_key] = {}

            # Réinitialiser estimation, contract, dollar pour toutes les semaines
            for week_number in range(1, 6):
                week_key = str(week_number)
                if week_key not in rpo_data['weekly'][month_key]:
                    rpo_data['weekly'][month_key][week_key] = {}

                # Garder h_marketing s'il existe, sinon initialiser à "-"
                if 'h_marketing' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['h_marketing'] = '-'

                # Garder prod_horaire s'il existe, sinon initialiser à "-" (EXACTEMENT comme h_marketing)
                if 'prod_horaire' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['prod_horaire'] = '-'

                # Initialiser commentaire et rating s'ils n'existent pas
                if 'commentaire' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['commentaire'] = 'Problème: - | Focus: -'
                if 'rating' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['rating'] = 0

                # Réinitialiser le reste (SANS prod_horaire car on le garde comme h_marketing)
                rpo_data['weekly'][month_key][week_key]['estimation'] = 0
                rpo_data['weekly'][month_key][week_key]['contract'] = 0
                rpo_data['weekly'][month_key][week_key]['dollar'] = 0
                rpo_data['weekly'][month_key][week_key]['depot'] = 0
                rpo_data['weekly'][month_key][week_key]['peintre'] = 0
                rpo_data['weekly'][month_key][week_key]['ca_cumul'] = 0
                rpo_data['weekly'][month_key][week_key]['produit'] = 0
                rpo_data['weekly'][month_key][week_key]['satisfaction'] = 0

        # Déterminer le chemin de base selon l'OS
        if sys.platform == 'win32':
            # Windows - remonter à la racine du projet (3 niveaux depuis QE/Backend/rpo.py)
            base_cloud = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        else:
            # Unix/Linux (Production sur Render)
            # Utiliser la variable d'environnement STORAGE_PATH si définie, sinon /mnt/cloud
            base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")

        # 1. Lire soumissions_completes (Estimation réel)
        soumissions_completes_path = os.path.join(base_cloud, "soumissions_completes", username, "soumissions.json")
        print(f"[DEBUG] [RPO SYNC] Chemin soumissions_completes: {soumissions_completes_path}", flush=True)
        print(f"[DEBUG] [RPO SYNC] Fichier existe? {os.path.exists(soumissions_completes_path)}", flush=True)

        if os.path.exists(soumissions_completes_path):
            with open(soumissions_completes_path, 'r', encoding='utf-8') as f:
                soumissions_completes = json.load(f)

            print(f"[INFO] [RPO SYNC] {len(soumissions_completes)} soumissions completes trouvees pour {username}", flush=True)

            for soumission in soumissions_completes:
                date_str = soumission.get('date', '')
                print(f"  [DATE] [RPO SYNC] Soumission date: {date_str}", flush=True)
                if date_str:
                    month_idx, week_num = get_week_number_from_date(date_str)
                    month_key = str(month_idx)
                    week_key = str(week_num)
                    print(f"    -> [RPO SYNC] Month index: {month_idx}, Week: {week_num}", flush=True)

                    if month_key in rpo_data['weekly'] and week_key in rpo_data['weekly'][month_key]:
                        rpo_data['weekly'][month_key][week_key]['estimation'] += 1
                        print(f"    [OK] [RPO SYNC] Ajoute a semaine {week_num} du mois {month_idx}", flush=True)
                    else:
                        print(f"    [WARN] [RPO SYNC] Mois {month_key} ou semaine {week_key} non trouve dans RPO", flush=True)
        else:
            print(f"[WARN] [RPO SYNC] Fichier soumissions_completes non trouve pour {username}", flush=True)

        # Charger les clients perdus pour les exclure du RPO
        clients_perdus_path = os.path.join(base_cloud, "clients_perdus", username, "clients.json")
        clients_perdus_ids = set()
        clients_perdus_count = 0
        if os.path.exists(clients_perdus_path):
            try:
                with open(clients_perdus_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        clients_perdus = json.loads(content)
                        clients_perdus_count = len(clients_perdus)
                        # Créer un set d'identifiants pour vérification rapide
                        for client in clients_perdus:
                            # Stocker id, num
                            if client.get('id'):
                                clients_perdus_ids.add(client.get('id'))
                            if client.get('num'):
                                clients_perdus_ids.add(client.get('num'))

                            # Composite keys - gérer les deux formats possibles
                            prenom = client.get('prenom') or client.get('clientPrenom', '')
                            nom = client.get('nom') or client.get('clientNom', '')
                            telephone = client.get('telephone', '')

                            if prenom or nom or telephone:
                                composite = f"{prenom}_{nom}_{telephone}".lower()
                                clients_perdus_ids.add(composite)
                                print(f"  [CLIENT PERDU] Ajout: {prenom} {nom} (num: {client.get('num')}, composite: {composite})", flush=True)

                print(f"[INFO] [RPO SYNC] {clients_perdus_count} clients perdus, {len(clients_perdus_ids)} identifiants charges", flush=True)
            except Exception as e:
                print(f"[WARN] [RPO SYNC] Erreur chargement clients perdus: {e}", flush=True)
        else:
            print(f"[INFO] [RPO SYNC] Aucun fichier clients_perdus trouve pour {username}", flush=True)

        # 2. Lire soumissions_signees (Contrat réel + $ réel)
        soumissions_signees_path = os.path.join(base_cloud, "soumissions_signees", username, "soumissions.json")
        if os.path.exists(soumissions_signees_path):
            with open(soumissions_signees_path, 'r', encoding='utf-8') as f:
                soumissions_signees = json.load(f)

            print(f"[INFO] [RPO SYNC] {len(soumissions_signees)} soumissions signees trouvees pour {username}", flush=True)

            for soumission in soumissions_signees:
                # VÉRIFIER SI CE CLIENT EST PERDU
                soumission_id = soumission.get('id')
                soumission_num = soumission.get('num')

                # Gérer les deux formats possibles: prenom/nom OU clientPrenom/clientNom
                prenom = soumission.get('prenom') or soumission.get('clientPrenom', '')
                nom = soumission.get('nom') or soumission.get('clientNom', '')
                telephone = soumission.get('telephone', '')

                soumission_composite = f"{prenom}_{nom}_{telephone}".lower()

                # Si le client est perdu, on le saute
                is_perdu = (soumission_id in clients_perdus_ids or
                            soumission_num in clients_perdus_ids or
                            soumission_composite in clients_perdus_ids)

                if is_perdu:
                    prix_str = soumission.get('prix', '0')
                    print(f"  [SKIP] [RPO SYNC] Client perdu exclu: {prenom} {nom} ({soumission_num}) - Prix: {prix_str}", flush=True)
                    continue

                date_str = soumission.get('date', '')
                prix_str = soumission.get('prix', '0')

                # Parser le prix (format: "1 000,00 $" ou "1 500,00 $" ou "1000")
                # Étape 1: Retirer tous les espaces (normaux et non-breakable), $, et remplacer , par .
                import re
                prix_clean = re.sub(r'\s+', '', prix_str)  # Retire tous les espaces (normaux + \xa0)
                prix_clean = prix_clean.replace('$', '').replace(',', '.')
                try:
                    prix = float(prix_clean)
                    print(f"  [PRIX] [RPO SYNC] Prix parse: {prix_str} = {prix}$", flush=True)
                except Exception as e:
                    print(f"  [ERREUR PRIX] [RPO SYNC] Impossible de parser: {e}", flush=True)
                    prix = 0

                print(f"  [DATE] [RPO SYNC] Soumission signee date: {date_str}", flush=True)
                if date_str:
                    month_idx, week_num = get_week_number_from_date(date_str)
                    month_key = str(month_idx)
                    week_key = str(week_num)
                    print(f"    -> [RPO SYNC] Month index: {month_idx}, Week: {week_num}", flush=True)

                    if month_key in rpo_data['weekly'] and week_key in rpo_data['weekly'][month_key]:
                        rpo_data['weekly'][month_key][week_key]['contract'] += 1
                        rpo_data['weekly'][month_key][week_key]['dollar'] += prix
                        print(f"    [OK] [RPO SYNC] +1 contract, +{prix}$ a semaine {week_num} du mois {month_idx}", flush=True)
                    else:
                        print(f"    [WARN] [RPO SYNC] Mois {month_key} ou semaine {week_key} non trouve dans RPO", flush=True)

        # 3. Synchroniser les dépôts depuis facturation_qe_periodes
        periodes_path = os.path.join(base_cloud, "facturation_qe_periodes", "periodes.json")
        if os.path.exists(periodes_path):
            with open(periodes_path, 'r', encoding='utf-8') as f:
                periodes_data = json.load(f)

            print(f"[INFO] [RPO SYNC] Synchronisation des depots depuis facturation_qe_periodes", flush=True)
            depot_count = 0

            # Parcourir toutes les périodes
            for periode_key, paiements in periodes_data.items():
                for paiement in paiements:
                    # Filtrer uniquement les dépôts pour cet entrepreneur
                    if (paiement.get('entrepreneurUsername') == username and
                        paiement.get('type') == 'depot' and
                        paiement.get('statut') in ['valide', 'traite', 'traite_attente_final', 'attente_comptable']):

                        date_str = paiement.get('date', '')
                        montant_str = paiement.get('montant', '0')

                        # Parser le montant (format: "431,16 $")
                        import re
                        montant_clean = re.sub(r'\s+', '', montant_str)
                        montant_clean = montant_clean.replace('$', '').replace(',', '.')
                        try:
                            montant = float(montant_clean)
                        except:
                            montant = 0

                        # Parser la date (format: "10/03/2026 16:25")
                        if date_str and montant > 0:
                            try:
                                date_parts = date_str.split(' ')[0]  # Prendre juste la date sans l'heure
                                # Convertir DD/MM/YYYY vers YYYY-MM-DD
                                day, month, year = date_parts.split('/')
                                date_formatted = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                                month_idx, week_num = get_week_number_from_date(date_formatted)
                                month_key = str(month_idx)
                                week_key = str(week_num)

                                if month_key in rpo_data['weekly'] and week_key in rpo_data['weekly'][month_key]:
                                    rpo_data['weekly'][month_key][week_key]['depot'] += montant
                                    depot_count += 1
                                    print(f"  [DEPOT] [RPO SYNC] +{montant}$ depot a semaine {week_num} du mois {month_idx} (date: {date_formatted})", flush=True)
                            except Exception as e:
                                print(f"  [WARN] [RPO SYNC] Erreur parsing date depot '{date_str}': {e}", flush=True)

            print(f"[INFO] [RPO SYNC] {depot_count} depots synchronises", flush=True)

        # 3b. Synchroniser les ventes produites depuis data/ventes_produit
        ventes_produit_path = os.path.join(base_cloud, "ventes_produit", username, "ventes.json")
        if os.path.exists(ventes_produit_path):
            with open(ventes_produit_path, 'r', encoding='utf-8') as f:
                ventes_produit = json.load(f)

            print(f"[INFO] [RPO SYNC] Synchronisation des ventes produites", flush=True)
            produit_count = 0

            for vente in ventes_produit:
                date_str = vente.get('date', '')
                prix_str = vente.get('prix', '0')

                # Parser le prix (même logique que pour les contrats signés)
                import re
                prix_clean = re.sub(r'\s+', '', prix_str)
                prix_clean = prix_clean.replace('$', '').replace(',', '.')
                try:
                    prix = float(prix_clean)
                except:
                    prix = 0

                # Parser la date (format: DD/MM/YYYY)
                if date_str and prix > 0:
                    try:
                        date_parts = date_str.split(' ')[0]  # Prendre juste la date sans l'heure
                        # Convertir DD/MM/YYYY vers YYYY-MM-DD
                        day, month, year = date_parts.split('/')
                        date_formatted = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                        month_idx, week_num = get_week_number_from_date(date_formatted)
                        month_key = str(month_idx)
                        week_key = str(week_num)

                        if month_key in rpo_data['weekly'] and week_key in rpo_data['weekly'][month_key]:
                            rpo_data['weekly'][month_key][week_key]['produit'] += prix
                            produit_count += 1
                            print(f"  [PRODUIT] [RPO SYNC] +{prix}$ produit a semaine {week_num} du mois {month_idx} (date: {date_formatted})", flush=True)
                    except Exception as e:
                        print(f"  [WARN] [RPO SYNC] Erreur parsing date vente produite '{date_str}': {e}", flush=True)

            print(f"[INFO] [RPO SYNC] {produit_count} ventes produites synchronisees", flush=True)

        # 4. Synchroniser les employés (peintres) depuis data/employes
        employes_path_base = os.path.join(base_cloud, "employes", username)
        if os.path.exists(employes_path_base):
            print(f"[INFO] [RPO SYNC] Synchronisation des employes (peintres) - MODE CUMULATIF", flush=True)

            # Collecter tous les peintres avec leur date d'activation
            peintres_list = []
            employe_files = ['nouveaux.json', 'actifs.json', 'inactifs.json']
            statuts_valides = ['En attente de validation', 'En attente comptable', 'Actif']

            for file_name in employe_files:
                file_path = os.path.join(employes_path_base, file_name)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            employes = json.load(f)

                        for employe in employes:
                            poste = employe.get('poste', '').lower()
                            poste_service = employe.get('posteService', '').lower()
                            statut = employe.get('statut', '')
                            date_activation_str = employe.get('dateActivation', '')

                            if (('peintre' in poste or 'peintre' in poste_service) and
                                statut in statuts_valides and
                                date_activation_str):

                                try:
                                    # Parser la date d'activation
                                    if '/' in date_activation_str:
                                        day, month, year = date_activation_str.split('/')
                                        date_formatted = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                    else:
                                        date_formatted = date_activation_str

                                    peintres_list.append({
                                        'date': date_formatted,
                                        'nom': employe.get('nom', 'Inconnu'),
                                        'statut': statut
                                    })
                                except Exception as e:
                                    print(f"  [WARN] [RPO SYNC] Erreur parsing date activation '{date_activation_str}': {e}", flush=True)

                    except Exception as e:
                        print(f"  [WARN] [RPO SYNC] Erreur lecture fichier employes '{file_name}': {e}", flush=True)

            # Trier les peintres par date d'activation
            peintres_list.sort(key=lambda x: x['date'])

            print(f"[INFO] [RPO SYNC] {len(peintres_list)} peintres trouves au total", flush=True)

            # Pour chaque semaine, compter CUMULATIVEMENT tous les peintres activés jusqu'à cette semaine
            from datetime import datetime
            for month_idx in all_months:
                month_key = str(month_idx)
                if month_key in rpo_data['weekly']:
                    for week_number in range(1, 6):
                        week_key = str(week_number)
                        if week_key in rpo_data['weekly'][month_key]:
                            # Trouver la date de fin de cette semaine
                            # On utilise la date du dimanche de cette semaine pour comparer
                            week_data_temp = rpo_data['weekly'][month_key][week_key]

                            # Calculer une date approximative pour cette semaine
                            # Mois -2 = Oct 2025, 0 = Jan 2026, 1 = Feb 2026, etc.
                            if month_idx == -2:
                                year = 2025
                                month = 10
                            elif month_idx == -1:
                                year = 2025
                                month = 11
                            else:
                                year = 2026
                                month = month_idx + 1

                            # Approximation: semaine X = jour (X * 7)
                            day = min(week_number * 7, 28)

                            try:
                                week_end_date = datetime(year, month, day)
                                week_end_str = week_end_date.strftime('%Y-%m-%d')

                                # Compter tous les peintres activés jusqu'à cette date
                                cumulative_count = sum(1 for p in peintres_list if p['date'] <= week_end_str)

                                rpo_data['weekly'][month_key][week_key]['peintre'] = cumulative_count

                                if cumulative_count > 0:
                                    print(f"  [PEINTRE CUMULATIF] Mois {month_idx}, Semaine {week_number}: {cumulative_count} peintres au total", flush=True)
                            except:
                                pass

            print(f"[INFO] [RPO SYNC] Synchronisation cumulative des peintres terminee", flush=True)

        # 5. Agréger les données hebdomadaires vers les totaux annuels
        print(f"[SYNC] [RPO SYNC] Aggregation des donnees hebdomadaires vers annuel...", flush=True)

        total_estimation = 0
        total_contract = 0
        total_dollar = 0
        total_hr_pap = 0

        for month_idx in all_months:
            month_key = str(month_idx)
            if month_key in rpo_data['weekly']:
                for week_number in range(1, 6):
                    week_key = str(week_number)
                    if week_key in rpo_data['weekly'][month_key]:
                        week_data = rpo_data['weekly'][month_key][week_key]
                        total_estimation += week_data.get('estimation', 0)
                        total_contract += week_data.get('contract', 0)
                        total_dollar += week_data.get('dollar', 0)

                        # Agréger h_marketing (ignorer les valeurs "-" et vides)
                        h_marketing = week_data.get('h_marketing', '-')
                        if h_marketing not in ['-', '', None]:
                            try:
                                total_hr_pap += float(h_marketing)
                            except (ValueError, TypeError):
                                pass

        # Mettre à jour les totaux annuels
        rpo_data['annual']['estimation_reel'] = total_estimation
        rpo_data['annual']['contract_reel'] = total_contract
        rpo_data['annual']['dollar_reel'] = total_dollar
        rpo_data['annual']['hr_pap_reel'] = total_hr_pap

        # Calculer le taux de vente réel (contract / estimation * 100)
        if total_estimation > 0:
            rpo_data['annual']['vente_reel'] = round((total_contract / total_estimation) * 100, 1)
        else:
            rpo_data['annual']['vente_reel'] = 0

        # Calculer le contrat moyen réel (dollar / contract)
        if total_contract > 0:
            rpo_data['annual']['moyen_reel'] = round(total_dollar / total_contract, 2)
        else:
            rpo_data['annual']['moyen_reel'] = 0

        print(f"[SYNC] [RPO SYNC] Totaux annuels agregés:", flush=True)
        print(f"  - H de PÀP: {total_hr_pap}h", flush=True)
        print(f"  - Estimations: {total_estimation}", flush=True)
        print(f"  - Contracts: {total_contract}", flush=True)
        print(f"  - Dollars: {total_dollar}", flush=True)
        print(f"  - Taux vente: {rpo_data['annual']['vente_reel']}%", flush=True)
        print(f"  - Contrat moyen: {rpo_data['annual']['moyen_reel']}$", flush=True)

        # Calculer le chiffre d'affaires cumulatif (ca_cumul) pour chaque semaine
        print(f"[SYNC] [RPO SYNC] Calcul chiffre d'affaires cumulatif...", flush=True)
        cumulative_revenue = 0
        for month_idx in all_months:
            month_key = str(month_idx)
            if month_key in rpo_data['weekly']:
                for week_number in range(1, 6):
                    week_key = str(week_number)
                    if week_key in rpo_data['weekly'][month_key]:
                        week_data = rpo_data['weekly'][month_key][week_key]
                        dollar = week_data.get('dollar', 0)

                        # Ajouter les dollars de cette semaine au cumul
                        cumulative_revenue += dollar

                        # Enregistrer le cumul dans cette semaine
                        rpo_data['weekly'][month_key][week_key]['ca_cumul'] = cumulative_revenue

                        if cumulative_revenue > 0:
                            print(f"  [CA CUMUL] Mois {month_idx}, Semaine {week_number}: {cumulative_revenue:.0f}$ cumulatif", flush=True)

        print(f"[INFO] [RPO SYNC] Chiffre d'affaires cumulatif final: {cumulative_revenue:.0f}$", flush=True)

        # 6. Synchroniser les avis clients pour calculer la satisfaction cumulative
        print(f"[SYNC] [RPO SYNC] Calcul satisfaction cumulative...", flush=True)
        reviews_path = os.path.join(base_cloud, "reviews", username, "reviews.json")
        all_reviews = []

        if os.path.exists(reviews_path):
            with open(reviews_path, 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)

            # Collecter tous les avis avec leurs dates
            for review in reviews_data:
                timestamp_str = review.get('timestamp', '')
                rating = review.get('rating', 0)

                if timestamp_str and rating > 0:
                    try:
                        # Parser le timestamp ISO 8601
                        review_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        review_date_str = review_date.strftime('%Y-%m-%d')
                        all_reviews.append({'date': review_date_str, 'rating': rating})
                        print(f"  [REVIEW] Avis trouve: {rating} etoiles le {review_date_str}", flush=True)
                    except Exception as e:
                        print(f"  [WARNING] Erreur parsing timestamp review: {e}", flush=True)
                        continue

        # Trier les avis par date
        all_reviews.sort(key=lambda x: x['date'])

        # Pour chaque semaine, calculer la moyenne cumulative des avis jusqu'à cette semaine
        # Créer une liste de toutes les semaines dans l'ordre chronologique
        weeks_in_order = []
        for month_idx in all_months:
            for week_number in range(1, 6):
                weeks_in_order.append((month_idx, week_number))

        cumulative_reviews = []
        for month_idx, week_number in weeks_in_order:
            month_key = str(month_idx)
            week_key = str(week_number)

            if month_key in rpo_data['weekly'] and week_key in rpo_data['weekly'][month_key]:
                # Ajouter tous les avis de cette semaine au cumul
                for review in all_reviews:
                    try:
                        review_month, review_week = get_week_number_from_date(review['date'])
                        if review_month == month_idx and review_week == week_number:
                            cumulative_reviews.append(review['rating'])
                    except:
                        pass

                # Calculer la moyenne cumulative
                if cumulative_reviews:
                    avg_rating = sum(cumulative_reviews) / len(cumulative_reviews)
                    rpo_data['weekly'][month_key][week_key]['satisfaction'] = round(avg_rating, 2)
                    print(f"  [SATISFACTION] Mois {month_idx}, Semaine {week_number}: {avg_rating:.2f} etoiles ({len(cumulative_reviews)} avis cumulatifs)", flush=True)
                else:
                    rpo_data['weekly'][month_key][week_key]['satisfaction'] = 0

        # Sauvegarder les données RPO mises à jour
        save_user_rpo_data(username, rpo_data)
        print(f"[OK] [RPO SYNC] Synchronisation soumissions -> RPO reussie pour {username}", flush=True)

        # Vérifier et attribuer automatiquement les badges basés sur les données RPO
        try:
            from gamification import check_and_award_automatic_badges
            badge_result = check_and_award_automatic_badges(username)
            if badge_result.get('awarded_badges'):
                print(f"[RPO SYNC] {len(badge_result['awarded_badges'])} badges automatiques attribues (+{badge_result['total_xp']} XP)", flush=True)
        except Exception as badge_error:
            print(f"[WARN] [RPO SYNC] Erreur verification badges automatiques: {badge_error}", flush=True)

        # Synchroniser le RPO du coach si cet entrepreneur est assigné à un coach
        try:
            from QE.Backend.coach_access import get_coach_for_entrepreneur
            coach_username = get_coach_for_entrepreneur(username)
            if coach_username:
                print(f"[RPO SYNC] Synchronisation RPO du coach {coach_username}...", flush=True)
                sync_coach_rpo(coach_username)
        except Exception as coach_sync_error:
            print(f"[WARN] [RPO SYNC] Erreur synchronisation RPO coach: {coach_sync_error}", flush=True)

        return True

    except Exception as e:
        print(f"[ERREUR] [RPO SYNC] Erreur sync soumissions -> RPO pour {username}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False


# ========================================
# ÉTATS DES RÉSULTATS
# ========================================

def update_etats_resultats_budget(username: str, budget_percent_data: Dict[str, float]) -> bool:
    """
    Met à jour les pourcentages Budget des États des Résultats
    budget_percent_data: dictionnaire {category: percent}
    """
    rpo_data = load_user_rpo_data(username)

    if 'etats_resultats' not in rpo_data:
        rpo_data['etats_resultats'] = {}

    rpo_data['etats_resultats']['budget_percent'] = budget_percent_data
    return save_user_rpo_data(username, rpo_data)


def get_etats_resultats_budget(username: str) -> Dict[str, float]:
    """Récupère les pourcentages Budget des États des Résultats"""
    rpo_data = load_user_rpo_data(username)
    return rpo_data.get('etats_resultats', {}).get('budget_percent', {})


def update_etats_resultats_actuel(username: str, actuel_data: Dict[str, float], cible_data: Dict[str, float] = None, budget_percent: Dict[str, float] = None) -> bool:
    """
    Met à jour les montants Actuel et CIBLÉ des États des Résultats
    actuel_data: dictionnaire {category: montant}
    cible_data: dictionnaire {category: montant} (optionnel)
    budget_percent: dictionnaire {category: pourcentage} (optionnel)
    """
    rpo_data = load_user_rpo_data(username)

    if 'etats_resultats' not in rpo_data:
        rpo_data['etats_resultats'] = {}

    rpo_data['etats_resultats']['actuel'] = actuel_data

    # Sauvegarder aussi les données CIBLÉ si fournies
    if cible_data is not None:
        rpo_data['etats_resultats']['cible'] = cible_data

    # Sauvegarder aussi les pourcentages personnalisés si fournis
    if budget_percent is not None:
        rpo_data['etats_resultats']['budget_percent'] = budget_percent

    return save_user_rpo_data(username, rpo_data)


def get_etats_resultats_actuel(username: str) -> Dict[str, Any]:
    """Récupère les montants Actuel et CIBLÉ des États des Résultats"""
    rpo_data = load_user_rpo_data(username)
    etats_resultats = rpo_data.get('etats_resultats', {})
    return {
        'actuel': etats_resultats.get('actuel', {}),
        'cible': etats_resultats.get('cible', {}),
        'budget_percent': etats_resultats.get('budget_percent', {})
    }


def sync_ventes_produit_to_rpo(username: str) -> Dict[str, Any]:
    """
    Synchronise les ventes produit dans les semaines du RPO
    Lit ventes_produit/{username}/ventes.json et met à jour le champ 'dollar' des semaines correspondantes

    Returns:
        Dict avec status et statistiques de synchronisation
    """
    import sys

    # Déterminer le chemin vers ventes_produit
    if sys.platform == 'win32':
        ventes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'ventes_produit', username)
    else:
        base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
        ventes_dir = os.path.join(base_cloud, "ventes_produit", username)

    ventes_file = os.path.join(ventes_dir, "ventes.json")

    if not os.path.exists(ventes_file):
        return {"status": "no_ventes", "message": f"Aucun fichier de ventes pour {username}"}

    # Charger les ventes produit
    try:
        with open(ventes_file, 'r', encoding='utf-8') as f:
            ventes = json.load(f)
    except Exception as e:
        return {"status": "error", "message": f"Erreur lecture ventes: {e}"}

    # Charger le RPO
    rpo_data = load_user_rpo_data(username)

    # Définir les semaines (même structure que le frontend)
    # Semaine 0 = 4 novembre 2025
    start_date = datetime(2025, 11, 4, tzinfo=TORONTO_TZ)

    # Initialiser les montants par semaine - RESET complet à 0
    week_dollars = {}
    for i in range(56):
        week_dollars[i] = 0

    ventes_synced = 0

    for vente in ventes:
        try:
            # Récupérer la date de complétion
            date_str = vente.get('date_completion')
            if not date_str:
                continue

            # Parser la date
            vente_date = parse_date_toronto(date_str)

            # Calculer le nombre de jours depuis le début
            delta = (vente_date - start_date).days

            # Calculer l'index de la semaine (0-55)
            week_index = delta // 7

            # Vérifier que la semaine est dans la plage valide
            if week_index < 0 or week_index >= 56:
                continue

            # Récupérer le prix
            prix_str = vente.get('prix', '0')
            prix_str = str(prix_str).replace('\xa0', '').replace(' ', '').replace('$', '').replace(',', '.')
            prix_num = float(prix_str)

            # Ajouter au montant de cette semaine
            week_dollars[week_index] += prix_num
            ventes_synced += 1

        except Exception as e:
            print(f"[SYNC RPO] Erreur traitement vente {vente.get('id', '?')}: {e}")
            continue

    # Mettre à jour le RPO avec les montants calculés
    # Mapper week_index (0-55) vers month_key et week_key
    week_counter = 0
    for month_index in range(-2, 11):  # Nov 2025 (-2) à Oct 2026 (10)
        month_key = str(month_index)

        if month_key not in rpo_data['weekly']:
            rpo_data['weekly'][month_key] = {}

        # 4-5 semaines par mois
        weeks_in_month = 5 if month_index in [-2, 0, 3, 5, 8, 10] else 4

        for week_num in range(1, weeks_in_month + 1):
            if week_counter >= 56:
                break

            week_key = str(week_num)

            # Créer la semaine si elle n'existe pas
            if week_key not in rpo_data['weekly'][month_key]:
                rpo_data['weekly'][month_key][week_key] = {}

            # Mettre à jour le montant dollar (même si c'est 0, pour reset les ventes perdues)
            rpo_data['weekly'][month_key][week_key]['dollar'] = week_dollars[week_counter]

            week_counter += 1

    # Sauvegarder le RPO mis à jour
    save_success = save_user_rpo_data(username, rpo_data)

    return {
        "status": "success" if save_success else "error",
        "ventes_synced": ventes_synced,
        "weeks_updated": len([d for d in week_dollars.values() if d > 0]),
        "total_montant": sum(week_dollars.values())
    }
