"""
Backend routes pour RPO (Résultats, Prévisions, Objectifs)
Gère les données annuelles, mensuelles et hebdomadaires par utilisateur
"""

import json
import os
import logging
import threading
import sys
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# Locks pour éviter les synchronisations simultanées
_coach_sync_locks = {}  # Dict[coach_username, Lock]
_direction_sync_lock = threading.Lock()
_locks_lock = threading.Lock()  # Lock pour accéder au dict des locks

# Locks pour éviter les écritures simultanées aux fichiers RPO (par utilisateur)
# threading.Lock protège au sein d'un même processus
_user_file_locks = {}  # Dict[username, Lock]
_user_file_locks_lock = threading.Lock()  # Lock pour accéder au dict des locks

def get_user_file_lock(username: str) -> threading.Lock:
    """Retourne un lock spécifique pour le fichier RPO d'un utilisateur"""
    with _user_file_locks_lock:
        if username not in _user_file_locks:
            _user_file_locks[username] = threading.Lock()
        return _user_file_locks[username]


def _acquire_file_lock(lock_path: str, timeout: float = 30.0):
    """
    Acquiert un file lock inter-processus.
    Sur Linux/Render: utilise fcntl.flock (bloquant)
    Sur Windows: utilise msvcrt.locking (polling)
    Retourne le file descriptor ouvert (à fermer pour libérer le lock).
    """
    import time

    # Créer le fichier lock s'il n'existe pas
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    fd = open(lock_path, 'w')

    if sys.platform == 'win32':
        # Windows: utiliser msvcrt.locking
        import msvcrt
        start = time.monotonic()
        while True:
            try:
                msvcrt.locking(fd.fileno(), msvcrt.LK_NBLCK, 1)
                return fd
            except (IOError, OSError):
                if time.monotonic() - start > timeout:
                    fd.close()
                    raise TimeoutError(f"Timeout acquiring file lock: {lock_path}")
                time.sleep(0.05)
    else:
        # Linux/Render: utiliser fcntl.flock (bloquant)
        import fcntl
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX)
        return fd


def _release_file_lock(fd):
    """Libère un file lock inter-processus."""
    try:
        if sys.platform == 'win32':
            import msvcrt
            try:
                msvcrt.locking(fd.fileno(), msvcrt.LK_UNLCK, 1)
            except:
                pass
        else:
            import fcntl
            fcntl.flock(fd.fileno(), fcntl.LOCK_UN)
    finally:
        fd.close()


@contextmanager
def rpo_file_lock(username: str):
    """
    Context manager qui verrouille le fichier RPO d'un utilisateur.
    Protège le cycle complet load -> modify -> save contre les race conditions.
    Combine un threading.Lock (intra-processus) et un file lock (inter-processus).
    """
    # 1. Lock intra-processus (threads dans le même worker uvicorn)
    thread_lock = get_user_file_lock(username)
    thread_lock.acquire()

    # 2. Lock inter-processus (entre workers uvicorn différents)
    filepath = get_user_rpo_file(username)
    lock_path = filepath + '.lock'
    fd = None
    try:
        fd = _acquire_file_lock(lock_path)
        yield
    finally:
        if fd:
            _release_file_lock(fd)
        thread_lock.release()

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


def get_user_role(username: str) -> str:
    """Récupère le rôle d'un utilisateur depuis la base de données"""
    try:
        import sqlite3
        from database import get_database_path
        DB_PATH = get_database_path()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE username=?", (username,))
            row = cursor.fetchone()
            if row:
                return row[0]
    except Exception as e:
        print(f"[RPO] Erreur get_user_role {username}: {e}")
    return "entrepreneur"


def get_user_rpo_file(username: str) -> str:
    """
    Retourne le chemin du fichier RPO pour un utilisateur
    NOTE: Tous les users direction partagent le même fichier direction_rpo.json
    """
    # Vérifier si c'est un user direction
    role = get_user_role(username)
    if role == "direction":
        return os.path.join(RPO_DATA_DIR, "direction_rpo.json")

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
                        "rating": 0,
                        "probleme": "-",
                        "focus": "-"
                    }
                    for week_num in range(1, 6)
                }
                for month_idx in [-2] + list(range(12))
            }
        }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # ALERTE: Fichier JSON corrompu - probablement une race condition
        print(f"[CRITICAL] [LOAD RPO] Fichier JSON corrompu pour {username}: {e}", flush=True)
        print(f"[CRITICAL] [LOAD RPO] Cela peut causer la perte des donnees annuelles!", flush=True)
        # Essayer de lire le fichier .tmp si il existe (backup de l'écriture atomique)
        temp_filepath = filepath + '.tmp'
        if os.path.exists(temp_filepath):
            try:
                with open(temp_filepath, 'r', encoding='utf-8') as f:
                    print(f"[RECOVERY] [LOAD RPO] Recuperation depuis fichier temporaire pour {username}", flush=True)
                    return json.load(f)
            except:
                pass
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
                        "rating": 0,
                        "probleme": "-",
                        "focus": "-"
                    }
                    for week_num in range(1, 6)
                }
                for month_idx in [-2] + list(range(12))
            }
        }


def save_user_rpo_data(username: str, data: Dict[str, Any]) -> bool:
    """
    Sauvegarde les données RPO d'un utilisateur.
    IMPORTANT: L'appelant DOIT utiliser rpo_file_lock(username) pour protéger
    le cycle complet load -> modify -> save. Cette fonction ne fait que l'écriture.
    """
    filepath = get_user_rpo_file(username)
    temp_filepath = filepath + '.tmp'

    print(f"[DEBUG] [SAVE RPO] Attempting to save for user: {username}", flush=True)
    print(f"[DEBUG] [SAVE RPO] Target filepath: {filepath}", flush=True)
    print(f"[DEBUG] [SAVE RPO] RPO_DATA_DIR: {RPO_DATA_DIR}", flush=True)
    print(f"[DEBUG] [SAVE RPO] Directory exists? {os.path.exists(os.path.dirname(filepath))}", flush=True)
    print(f"[DEBUG] [SAVE RPO] File exists before save? {os.path.exists(filepath)}", flush=True)

    try:
        # Ajouter timestamp de dernière modification (heure de Toronto)
        data['last_updated'] = get_toronto_now().isoformat()

        # Écriture atomique: écrire dans un fichier temporaire puis renommer
        with open(temp_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Renommer atomiquement (remplace le fichier existant)
        # Sur Windows avec OneDrive, os.replace peut échouer temporairement
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                os.replace(temp_filepath, filepath)
                break  # Succès
            except PermissionError as pe:
                if attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
                else:
                    # Fallback: écrire directement si os.replace échoue
                    print(f"[WARN] [SAVE RPO] os.replace failed, using fallback write", flush=True)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    if os.path.exists(temp_filepath):
                        try:
                            os.remove(temp_filepath)
                        except:
                            pass

        print(f"[DEBUG] [SAVE RPO] File written successfully!", flush=True)
        print(f"[DEBUG] [SAVE RPO] File exists after save? {os.path.exists(filepath)}", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] [SAVE RPO] Failed to save RPO for {username}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except:
                pass
        return False


def update_annual_data(username: str, annual_data: Dict[str, Any]) -> bool:
    """
    Met à jour les données annuelles (MERGE au lieu d'écraser)
    """
    with rpo_file_lock(username):
        rpo_data = load_user_rpo_data(username)

        # MERGE: préserver les données existantes et mettre à jour seulement les nouveaux champs
        if 'annual' not in rpo_data:
            rpo_data['annual'] = {}

        # Filtrer les champs qui sont calculés automatiquement par sync_soumissions_to_rpo()
        protected_fields = ['hr_pap_reel', 'estimation_reel', 'contract_reel', 'dollar_reel',
                           'hr_pap_reel_sans_week1', 'mktg_reel', 'vente_reel', 'moyen_reel', 'prod_horaire']

        # Mettre à jour seulement les champs NON protégés
        for key, value in annual_data.items():
            if key not in protected_fields:
                rpo_data['annual'][key] = value

        return save_user_rpo_data(username, rpo_data)


def update_monthly_data(username: str, month: str, monthly_data: Dict[str, Any]) -> bool:
    """
    Met à jour les données d'un mois spécifique
    month: 'jan', 'feb', 'mar', etc.
    """
    with rpo_file_lock(username):
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
    print(f"[BACKEND-SAVE] Reception des donnees pour {username}, mois {month_index}, semaine {week_number}", flush=True)
    print(f"[BACKEND-SAVE] Donnees recues: {weekly_data}", flush=True)
    if 'prod_horaire' in weekly_data:
        print(f"[BACKEND-SAVE] Prod Horaire: {weekly_data['prod_horaire']}$/h", flush=True)

    # Lock couvre le cycle complet load -> modify -> save
    with rpo_file_lock(username):
        rpo_data = load_user_rpo_data(username)

        if 'weekly' not in rpo_data:
            rpo_data['weekly'] = {}

        month_key = str(month_index)
        if month_key not in rpo_data['weekly']:
            rpo_data['weekly'][month_key] = {}

        week_key = str(week_number)

        # MERGE au lieu d'écraser
        if week_key in rpo_data['weekly'][month_key]:
            print(f"[BACKEND-SAVE] Merge avec donnees existantes pour semaine {week_number}", flush=True)
            existing_data = rpo_data['weekly'][month_key][week_key]
            existing_data.update(weekly_data)
            rpo_data['weekly'][month_key][week_key] = existing_data
        else:
            print(f"[BACKEND-SAVE] Creation nouvelle semaine {week_number}", flush=True)
            rpo_data['weekly'][month_key][week_key] = weekly_data

        result = save_user_rpo_data(username, rpo_data)

    # Ces opérations secondaires sont HORS du lock pour ne pas bloquer
    if result:
        print(f"[BACKEND-SAVE] Donnees sauvegardees avec succes", flush=True)

        # Synchroniser le RPO du coach si cet entrepreneur est assigné à un coach
        try:
            from QE.Backend.coach_access import get_coach_for_entrepreneur
            coach_username = get_coach_for_entrepreneur(username)
            if coach_username:
                print(f"[BACKEND-SAVE] Synchronisation RPO du coach {coach_username}...", flush=True)
                sync_coach_rpo(coach_username)
        except Exception as coach_sync_error:
            print(f"[WARN] [BACKEND-SAVE] Erreur synchronisation RPO coach: {coach_sync_error}", flush=True)

        # Vérifier et attribuer les badges automatiques
        try:
            from gamification import check_and_award_automatic_badges
            badge_result = check_and_award_automatic_badges(username)
            if badge_result.get('awarded_badges'):
                print(f"[BACKEND-SAVE] Badges attribues: {len(badge_result['awarded_badges'])} (+{badge_result['total_xp']} XP)", flush=True)
        except Exception as badge_error:
            print(f"[WARN] [BACKEND-SAVE] Erreur verification badges: {badge_error}", flush=True)
    else:
        print(f"[BACKEND-SAVE] Echec de la sauvegarde", flush=True)

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

            # Nettoyer les sections qui ne devraient PAS être dans le JSON direction
            # La direction n'a pas d'états des résultats
            if 'etats_resultats' in direction_rpo:
                del direction_rpo['etats_resultats']

            # La direction n'a pas de données monthly (seulement weekly)
            if 'monthly' in direction_rpo:
                del direction_rpo['monthly']

            # Supprimer team_metrics et entrepreneurs_metrics (obsolètes)
            if 'team_metrics' in direction_rpo:
                del direction_rpo['team_metrics']
            if 'team_previsions' in direction_rpo:
                del direction_rpo['team_previsions']
            if 'entrepreneurs_metrics' in direction_rpo:
                del direction_rpo['entrepreneurs_metrics']

            # Réinitialiser les données weekly de direction
            if 'weekly' not in direction_rpo:
                direction_rpo['weekly'] = {}

            # Nettoyer les anciens mois négatifs (-2, -1) s'ils existent
            if '-2' in direction_rpo['weekly']:
                del direction_rpo['weekly']['-2']
            if '-1' in direction_rpo['weekly']:
                del direction_rpo['weekly']['-1']

            # Initialiser toutes les semaines à 0 (seulement mois 0-11: Janvier-Décembre 2026)
            all_months = list(range(12))
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
                    # Ignorer les mois négatifs (-2, -1) lors de l'agrégation
                    if month_key in ['-2', '-1']:
                        continue

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

            # Charger et ajouter les prévisions direction dans le JSON
            try:
                from QE.Backend.direction_previsions import load_direction_metrics, get_direction_team_objectif_total

                # Coach previsions (métriques globales direction + objectif total)
                # Note: Le fichier direction_rpo.json est COMMUN à tous les utilisateurs direction
                direction_metrics = load_direction_metrics('direction')
                total_objectif = get_direction_team_objectif_total('direction')

                direction_rpo['coach_previsions'] = {
                    'cm': direction_metrics.get('cm', 0),
                    'ratioMktg': direction_metrics.get('ratioMktg', 0),
                    'tauxVente': direction_metrics.get('tauxVente', 0),
                    'totalObjectif': total_objectif
                }

                print(f"[DIRECTION RPO] Previsions ajoutees: Total={total_objectif}, CM={direction_metrics.get('cm')}", flush=True)

            except Exception as previsions_error:
                print(f"[WARN] [DIRECTION RPO] Erreur chargement previsions: {previsions_error}", flush=True)

            # Compter le nombre total d'entrepreneurs (via tous les coaches)
            total_entrepreneurs = 0
            try:
                from QE.Backend.coach_access import get_entrepreneurs_for_coach
                for coach_username in coaches:
                    entrepreneurs = get_entrepreneurs_for_coach(coach_username)
                    if entrepreneurs:
                        total_entrepreneurs += len(entrepreneurs)
            except Exception as count_error:
                print(f"[WARN] [DIRECTION RPO] Erreur comptage entrepreneurs: {count_error}", flush=True)

            # Calculer les totaux annuels à partir des données weekly agrégées
            print(f"[DIRECTION RPO] Calcul des totaux annuels...", flush=True)

            total_estimation = 0
            total_contract = 0
            total_dollar = 0
            total_hr_pap = 0
            total_hr_pap_sans_week1 = 0
            total_produit = 0

            for month_idx in all_months:
                month_key = str(month_idx)
                if month_key in direction_rpo['weekly']:
                    for week_number in range(1, 6):
                        week_key = str(week_number)
                        if week_key in direction_rpo['weekly'][month_key]:
                            week_data = direction_rpo['weekly'][month_key][week_key]
                            total_estimation += week_data.get('estimation', 0)
                            total_contract += week_data.get('contract', 0)
                            total_dollar += week_data.get('dollar', 0)
                            total_produit += week_data.get('produit', 0)

                            # Agréger h_marketing
                            h_marketing = week_data.get('h_marketing', 0)
                            if h_marketing and h_marketing != '-':
                                try:
                                    hr_val = float(h_marketing)
                                    total_hr_pap += hr_val
                                    # Exclure semaine 1 du mois 0 (formation)
                                    if not (month_idx == 0 and week_number == 1):
                                        total_hr_pap_sans_week1 += hr_val
                                except (ValueError, TypeError):
                                    pass

            # Initialiser annual si nécessaire
            if 'annual' not in direction_rpo:
                direction_rpo['annual'] = {}

            # Mettre à jour les totaux annuels
            direction_rpo['annual']['estimation_reel'] = total_estimation
            direction_rpo['annual']['contract_reel'] = total_contract
            direction_rpo['annual']['dollar_reel'] = total_dollar
            direction_rpo['annual']['hr_pap_reel'] = total_hr_pap
            direction_rpo['annual']['hr_pap_reel_sans_week1'] = total_hr_pap_sans_week1
            direction_rpo['annual']['produit_reel'] = total_produit
            direction_rpo['annual']['nb_entrepreneurs'] = total_entrepreneurs
            direction_rpo['annual']['nb_coaches'] = len(coaches)

            # Agréger les métriques par grade depuis tous les coaches
            total_estimation_recrue = 0
            total_estimation_senior = 0
            total_hr_pap_recrue = 0
            total_hr_pap_senior = 0
            total_nb_recrue = 0
            total_nb_senior = 0

            for coach_username in coaches:
                coach_rpo = load_user_rpo_data(coach_username)
                coach_annual = coach_rpo.get('annual', {})
                total_estimation_recrue += coach_annual.get('estimation_reel_recrue', 0) or 0
                total_estimation_senior += coach_annual.get('estimation_reel_senior', 0) or 0
                total_hr_pap_recrue += coach_annual.get('hr_pap_reel_recrue', 0) or 0
                total_hr_pap_senior += coach_annual.get('hr_pap_reel_senior', 0) or 0
                total_nb_recrue += coach_annual.get('nb_recrue', 0) or 0
                total_nb_senior += coach_annual.get('nb_senior', 0) or 0

            direction_rpo['annual']['estimation_reel_recrue'] = total_estimation_recrue
            direction_rpo['annual']['estimation_reel_senior'] = total_estimation_senior
            direction_rpo['annual']['hr_pap_reel_recrue'] = total_hr_pap_recrue
            direction_rpo['annual']['hr_pap_reel_senior'] = total_hr_pap_senior
            direction_rpo['annual']['nb_recrue'] = total_nb_recrue
            direction_rpo['annual']['nb_senior'] = total_nb_senior

            print(f"[DIRECTION RPO] Par grade: recrue={total_nb_recrue} (est={total_estimation_recrue}), senior={total_nb_senior} (est={total_estimation_senior})", flush=True)

            # Calculer le taux marketing réel (estimation / hr_pap sans semaine 1)
            if total_hr_pap_sans_week1 > 0:
                direction_rpo['annual']['mktg_reel'] = round(total_estimation / total_hr_pap_sans_week1, 2)
            else:
                direction_rpo['annual']['mktg_reel'] = 0

            # Calculer le taux de vente réel (contract / estimation * 100)
            if total_estimation > 0:
                direction_rpo['annual']['vente_reel'] = round((total_contract / total_estimation) * 100, 2)
            else:
                direction_rpo['annual']['vente_reel'] = 0

            # Calculer le contrat moyen réel (dollar / contract)
            if total_contract > 0:
                direction_rpo['annual']['moyen_reel'] = round(total_dollar / total_contract, 2)
            else:
                direction_rpo['annual']['moyen_reel'] = 0

            print(f"[DIRECTION RPO] Totaux annuels calculés:", flush=True)
            print(f"  - Hr PAP: {total_hr_pap}h (sans week1: {total_hr_pap_sans_week1}h)", flush=True)
            print(f"  - Estimations: {total_estimation}", flush=True)
            print(f"  - Contracts: {total_contract}", flush=True)
            print(f"  - Dollars: {total_dollar}$", flush=True)
            print(f"  - Taux MKG: {direction_rpo['annual']['mktg_reel']}", flush=True)
            print(f"  - Taux vente: {direction_rpo['annual']['vente_reel']}%", flush=True)

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

            # Nettoyer les sections qui ne devraient PAS être dans le JSON coach
            # Les coaches n'ont pas d'états des résultats
            if 'etats_resultats' in coach_rpo:
                del coach_rpo['etats_resultats']

            # Les coaches n'ont pas de données monthly (seulement weekly)
            if 'monthly' in coach_rpo:
                del coach_rpo['monthly']

            # Supprimer team_metrics (obsolète)
            if 'team_metrics' in coach_rpo:
                del coach_rpo['team_metrics']
            if 'team_previsions' in coach_rpo:
                del coach_rpo['team_previsions']

            # Réinitialiser les données weekly du coach
            if 'weekly' not in coach_rpo:
                coach_rpo['weekly'] = {}

            # Nettoyer les anciens mois négatifs (-2, -1) s'ils existent
            if '-2' in coach_rpo['weekly']:
                del coach_rpo['weekly']['-2']
            if '-1' in coach_rpo['weekly']:
                del coach_rpo['weekly']['-1']

            # Initialiser toutes les semaines avec h_marketing à 0 (seulement mois 0-11: Janvier-Décembre 2026)
            all_months = list(range(12))
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
                    # Ignorer les mois négatifs (-2, -1) lors de l'agrégation
                    if month_key in ['-2', '-1']:
                        continue

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

            # Charger et ajouter les prévisions coach dans le JSON
            try:
                from QE.Backend.coach_previsions import load_coach_previsions, load_coach_metrics, get_team_objectif_total

                # 1. Coach previsions (métriques globales + objectif total)
                coach_metrics = load_coach_metrics(coach_username)
                total_objectif = get_team_objectif_total(coach_username)

                coach_rpo['coach_previsions'] = {
                    'cm': coach_metrics.get('cm', 0),
                    'ratioMktg': coach_metrics.get('ratioMktg', 0),
                    'tauxVente': coach_metrics.get('tauxVente', 0),
                    'totalObjectif': total_objectif
                }

                # 2. Entrepreneurs metrics (objectifs et métriques par entrepreneur)
                previsions_entrepreneurs = load_coach_previsions(coach_username)
                entrepreneurs_metrics = {}

                for entrepreneur_username in entrepreneur_usernames:
                    entrepreneur_rpo = load_user_rpo_data(entrepreneur_username)
                    annual = entrepreneur_rpo.get('annual', {})

                    # Objectif CA: utiliser la prévision coach si définie, sinon l'objectif entrepreneur
                    objectif_ca = previsions_entrepreneurs.get(entrepreneur_username, annual.get('objectif_ca', 0))

                    entrepreneurs_metrics[entrepreneur_username] = {
                        'objectif_ca': objectif_ca,
                        'cm': annual.get('cm_prevision', 0),
                        'ratioMktg': annual.get('ratio_mktg', 0),
                        'tauxVente': annual.get('taux_vente', 0)
                    }

                coach_rpo['entrepreneurs_metrics'] = entrepreneurs_metrics

                print(f"[COACH RPO] Previsions ajoutees: Total={total_objectif}, CM={coach_metrics.get('cm')}, {len(entrepreneurs_metrics)} entrepreneurs", flush=True)

            except Exception as previsions_error:
                print(f"[WARN] [COACH RPO] Erreur chargement previsions: {previsions_error}", flush=True)

            # Calculer les totaux annuels à partir des données weekly agrégées
            print(f"[COACH RPO] Calcul des totaux annuels pour {coach_username}...", flush=True)

            total_estimation = 0
            total_contract = 0
            total_dollar = 0
            total_hr_pap = 0
            total_hr_pap_sans_week1 = 0
            total_produit = 0

            for month_idx in all_months:
                month_key = str(month_idx)
                if month_key in coach_rpo['weekly']:
                    for week_number in range(1, 6):
                        week_key = str(week_number)
                        if week_key in coach_rpo['weekly'][month_key]:
                            week_data = coach_rpo['weekly'][month_key][week_key]
                            total_estimation += week_data.get('estimation', 0)
                            total_contract += week_data.get('contract', 0)
                            total_dollar += week_data.get('dollar', 0)
                            total_produit += week_data.get('produit', 0)

                            # Agréger h_marketing
                            h_marketing = week_data.get('h_marketing', 0)
                            if h_marketing and h_marketing != '-':
                                try:
                                    hr_val = float(h_marketing)
                                    total_hr_pap += hr_val
                                    # Exclure semaine 1 du mois 0 (formation)
                                    if not (month_idx == 0 and week_number == 1):
                                        total_hr_pap_sans_week1 += hr_val
                                except (ValueError, TypeError):
                                    pass

            # Initialiser annual si nécessaire
            if 'annual' not in coach_rpo:
                coach_rpo['annual'] = {}

            # Mettre à jour les totaux annuels
            coach_rpo['annual']['estimation_reel'] = total_estimation
            coach_rpo['annual']['contract_reel'] = total_contract
            coach_rpo['annual']['dollar_reel'] = total_dollar
            coach_rpo['annual']['hr_pap_reel'] = total_hr_pap
            coach_rpo['annual']['hr_pap_reel_sans_week1'] = total_hr_pap_sans_week1
            coach_rpo['annual']['produit_reel'] = total_produit
            coach_rpo['annual']['nb_entrepreneurs'] = len(entrepreneur_usernames)

            # Calculer les métriques par grade (recrue vs senior)
            estimation_reel_recrue = 0
            estimation_reel_senior = 0
            hr_pap_reel_recrue = 0
            hr_pap_reel_senior = 0
            nb_recrue = 0
            nb_senior = 0

            # Déterminer le base_cloud pour user_info.json
            import sys
            if sys.platform == 'win32':
                base_cloud_info = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
            else:
                base_cloud_info = os.getenv("STORAGE_PATH", "/mnt/cloud")

            for entrepreneur_username in entrepreneur_usernames:
                # Charger user_info pour le grade
                user_info_path = os.path.join(base_cloud_info, "signatures", entrepreneur_username, "user_info.json")
                grade = ""
                if os.path.exists(user_info_path):
                    try:
                        with open(user_info_path, "r", encoding="utf-8") as f:
                            user_info = json.load(f)
                            grade = user_info.get("grade", "").lower()
                    except:
                        pass

                # Charger le RPO de l'entrepreneur pour son estimation_reel
                entrepreneur_rpo = load_user_rpo_data(entrepreneur_username)
                entrepreneur_annual = entrepreneur_rpo.get('annual', {})
                est_reel = entrepreneur_annual.get('estimation_reel', 0) or 0
                hr_pap = entrepreneur_annual.get('hr_pap_reel_sans_week1', 0) or 0

                if grade == "recrue":
                    estimation_reel_recrue += est_reel
                    hr_pap_reel_recrue += hr_pap
                    nb_recrue += 1
                elif grade in ["senior1", "senior2", "senior3"]:
                    estimation_reel_senior += est_reel
                    hr_pap_reel_senior += hr_pap
                    nb_senior += 1

            coach_rpo['annual']['estimation_reel_recrue'] = estimation_reel_recrue
            coach_rpo['annual']['estimation_reel_senior'] = estimation_reel_senior
            coach_rpo['annual']['hr_pap_reel_recrue'] = hr_pap_reel_recrue
            coach_rpo['annual']['hr_pap_reel_senior'] = hr_pap_reel_senior
            coach_rpo['annual']['nb_recrue'] = nb_recrue
            coach_rpo['annual']['nb_senior'] = nb_senior

            print(f"[COACH RPO] Par grade: recrue={nb_recrue} (est={estimation_reel_recrue}), senior={nb_senior} (est={estimation_reel_senior})", flush=True)

            # Calculer le taux marketing réel (estimation / hr_pap)
            if total_hr_pap > 0:
                coach_rpo['annual']['mktg_reel'] = round(total_estimation / total_hr_pap, 2)
            else:
                coach_rpo['annual']['mktg_reel'] = 0

            # Calculer le taux de vente réel (contract / estimation * 100)
            if total_estimation > 0:
                coach_rpo['annual']['vente_reel'] = round((total_contract / total_estimation) * 100, 2)
            else:
                coach_rpo['annual']['vente_reel'] = 0

            # Calculer le contrat moyen réel (dollar / contract)
            if total_contract > 0:
                coach_rpo['annual']['moyen_reel'] = round(total_dollar / total_contract, 2)
            else:
                coach_rpo['annual']['moyen_reel'] = 0

            print(f"[COACH RPO] Totaux annuels pour {coach_username}:", flush=True)
            print(f"  - Hr PAP: {total_hr_pap}h", flush=True)
            print(f"  - Estimations: {total_estimation}", flush=True)
            print(f"  - Taux MKG: {coach_rpo['annual']['mktg_reel']}", flush=True)

            # Sauvegarder le RPO du coach (contient données réelles agrégées + prévisions)
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

    _lock_held = False
    _sync_lock_ctx = None
    try:
        # Charger les données RPO existantes
        # Le lock est acquis manuellement pour couvrir load -> recalcul -> save
        _sync_lock_ctx = rpo_file_lock(username)
        _sync_lock_ctx.__enter__()
        _lock_held = True

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

                # Initialiser rating, probleme et focus s'ils n'existent pas
                if 'rating' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['rating'] = 0
                if 'probleme' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['probleme'] = '-'
                if 'focus' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['focus'] = '-'

                # Réinitialiser le reste (SANS prod_horaire car on le garde comme h_marketing)
                rpo_data['weekly'][month_key][week_key]['estimation'] = 0
                rpo_data['weekly'][month_key][week_key]['contract'] = 0
                rpo_data['weekly'][month_key][week_key]['dollar'] = 0
                rpo_data['weekly'][month_key][week_key]['ca_cumul'] = 0
                rpo_data['weekly'][month_key][week_key]['produit'] = 0

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

            # Filtrer les doublons par numéro de soumission (garder première occurrence)
            seen_nums = set()
            unique_soumissions = []
            for s in soumissions_completes:
                num = s.get('num', '')
                if num and num not in seen_nums:
                    seen_nums.add(num)
                    unique_soumissions.append(s)

            print(f"[INFO] [RPO SYNC] {len(soumissions_completes)} soumissions completes trouvees, {len(unique_soumissions)} uniques pour {username}", flush=True)

            for soumission in unique_soumissions:
                date_str = soumission.get('date', '')
                print(f"  [DATE] [RPO SYNC] Soumission {soumission.get('num', '')} date: {date_str}", flush=True)
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
        # IMPORTANT: On matche UNIQUEMENT par id et num (identifiants uniques du contrat)
        # PAS par nom/prénom/téléphone pour éviter d'exclure TOUS les contrats d'un même client
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
                        # UNIQUEMENT id et num - pas de composite par nom pour éviter les faux positifs
                        for client in clients_perdus:
                            # Stocker id et num (identifiants uniques du contrat)
                            if client.get('id'):
                                clients_perdus_ids.add(str(client.get('id')))
                            if client.get('num'):
                                clients_perdus_ids.add(str(client.get('num')))

                            prenom = client.get('prenom') or client.get('clientPrenom', '')
                            nom = client.get('nom') or client.get('clientNom', '')
                            print(f"  [CLIENT PERDU] Ajout: {prenom} {nom} (id: {client.get('id')}, num: {client.get('num')})", flush=True)

                print(f"[INFO] [RPO SYNC] {clients_perdus_count} clients perdus, {len(clients_perdus_ids)} identifiants charges (id/num uniquement)", flush=True)
            except Exception as e:
                print(f"[WARN] [RPO SYNC] Erreur chargement clients perdus: {e}", flush=True)
        else:
            print(f"[INFO] [RPO SYNC] Aucun fichier clients_perdus trouve pour {username}", flush=True)

        # 2. NOUVELLE LOGIQUE: Compter contrats/dollars depuis facturation_qe_statuts + ventes (acceptees + produit)
        # Un contrat est compté seulement quand le premier paiement est traité (datePremiereFacturation existe)
        # Le montant est le prix total de la vente (depuis ventes_acceptees OU ventes_produit)
        # La date utilisée est datePremiereFacturation

        import re

        # 2.1 Charger ventes_acceptees ET ventes_produit pour créer un lookup num -> prix total
        ventes_par_num = {}  # {num: {prix, prenom, nom, id}}

        # Charger ventes_acceptees
        ventes_acceptees_path = os.path.join(base_cloud, "ventes_acceptees", username, "ventes.json")
        if os.path.exists(ventes_acceptees_path):
            with open(ventes_acceptees_path, 'r', encoding='utf-8') as f:
                ventes_acceptees = json.load(f)

            print(f"[INFO] [RPO SYNC] {len(ventes_acceptees)} ventes acceptees trouvees pour {username}", flush=True)

            for vente in ventes_acceptees:
                num = vente.get('num', '')
                if num and num not in ventes_par_num:
                    prix_str = vente.get('prix', '0')
                    prix_clean = re.sub(r'\s+', '', str(prix_str))
                    prix_clean = prix_clean.replace('$', '').replace(',', '.')
                    try:
                        prix = float(prix_clean)
                    except:
                        prix = 0

                    ventes_par_num[num] = {
                        'prix': prix,
                        'prenom': vente.get('prenom') or vente.get('clientPrenom', ''),
                        'nom': vente.get('nom') or vente.get('clientNom', ''),
                        'id': vente.get('id', ''),
                        'source': 'ventes_acceptees'
                    }

        # Charger ventes_produit (ajouter celles qui ne sont pas déjà dans le lookup)
        ventes_produit_path = os.path.join(base_cloud, "ventes_produit", username, "ventes.json")
        if os.path.exists(ventes_produit_path):
            with open(ventes_produit_path, 'r', encoding='utf-8') as f:
                ventes_produit = json.load(f)

            print(f"[INFO] [RPO SYNC] {len(ventes_produit)} ventes produit trouvees pour {username}", flush=True)

            for vente in ventes_produit:
                num = vente.get('num', '')
                if num and num not in ventes_par_num:
                    prix_str = vente.get('prix', '0')
                    prix_clean = re.sub(r'\s+', '', str(prix_str))
                    prix_clean = prix_clean.replace('$', '').replace(',', '.')
                    try:
                        prix = float(prix_clean)
                    except:
                        prix = 0

                    ventes_par_num[num] = {
                        'prix': prix,
                        'prenom': vente.get('prenom') or vente.get('clientPrenom', ''),
                        'nom': vente.get('nom') or vente.get('clientNom', ''),
                        'id': vente.get('id', ''),
                        'source': 'ventes_produit'
                    }

        print(f"[INFO] [RPO SYNC] Lookup créé: {len(ventes_par_num)} ventes uniques par num (acceptees + produit)", flush=True)

        # 2.2 Charger facturation_qe_statuts pour trouver les clients avec datePremiereFacturation
        statuts_clients_path = os.path.join(base_cloud, "facturation_qe_statuts", username, "statuts_clients.json")

        if os.path.exists(statuts_clients_path):
            with open(statuts_clients_path, 'r', encoding='utf-8') as f:
                statuts_clients = json.load(f)

            print(f"[INFO] [RPO SYNC] {len(statuts_clients)} clients dans facturation_qe_statuts pour {username}", flush=True)

            contracts_counted = 0
            for num_soumission, statuts in statuts_clients.items():
                # Vérifier si datePremiereFacturation existe (= premier paiement traité)
                date_premiere_facturation = statuts.get('datePremiereFacturation')

                if not date_premiere_facturation:
                    print(f"  [SKIP] [RPO SYNC] {num_soumission}: Pas de datePremiereFacturation, non compté", flush=True)
                    continue

                # Vérifier si ce contrat est perdu
                is_perdu = num_soumission in clients_perdus_ids
                if is_perdu:
                    print(f"  [SKIP] [RPO SYNC] Contrat perdu exclu: {num_soumission}", flush=True)
                    continue

                # Récupérer le prix depuis ventes_acceptees
                vente_info = ventes_par_num.get(num_soumission)
                if not vente_info:
                    print(f"  [WARN] [RPO SYNC] {num_soumission}: datePremiereFacturation existe mais pas dans ventes_acceptees", flush=True)
                    continue

                prix = vente_info['prix']
                prenom = vente_info['prenom']
                nom = vente_info['nom']

                print(f"  [FACTURATION] [RPO SYNC] {num_soumission} ({prenom} {nom}): datePremiereFacturation={date_premiere_facturation}, prix={prix}$", flush=True)

                # Calculer la semaine RPO depuis datePremiereFacturation
                month_idx, week_num = get_week_number_from_date(date_premiere_facturation)
                month_key = str(month_idx)
                week_key = str(week_num)
                print(f"    -> [RPO SYNC] Month index: {month_idx}, Week: {week_num}", flush=True)

                if month_key in rpo_data['weekly'] and week_key in rpo_data['weekly'][month_key]:
                    rpo_data['weekly'][month_key][week_key]['contract'] += 1
                    rpo_data['weekly'][month_key][week_key]['dollar'] += prix
                    contracts_counted += 1
                    print(f"    [OK] [RPO SYNC] +1 contract, +{prix}$ a semaine {week_num} du mois {month_idx}", flush=True)
                else:
                    print(f"    [WARN] [RPO SYNC] Mois {month_key} ou semaine {week_key} non trouve dans RPO", flush=True)

            print(f"[INFO] [RPO SYNC] Total: {contracts_counted} contrats comptes depuis facturation_qe_statuts", flush=True)
        else:
            print(f"[INFO] [RPO SYNC] Aucun fichier facturation_qe_statuts trouve pour {username} - 0 contrats comptes", flush=True)

        # 3. Synchroniser les ventes produites depuis data/ventes_produit
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

        # 4. Agréger les données hebdomadaires vers les totaux annuels
        print(f"[SYNC] [RPO SYNC] Aggregation des donnees hebdomadaires vers annuel...", flush=True)

        total_estimation = 0
        total_contract = 0
        total_dollar = 0
        total_hr_pap = 0
        total_hr_pap_sans_week1 = 0  # Heures sans la semaine 1 (formation)

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
                                hr_val = float(h_marketing)
                                total_hr_pap += hr_val
                                # Exclure semaine 1 du mois 0 (5-11 janv = formation)
                                if not (month_idx == 0 and week_number == 1):
                                    total_hr_pap_sans_week1 += hr_val
                            except (ValueError, TypeError):
                                pass

        # Mettre à jour les totaux annuels
        rpo_data['annual']['estimation_reel'] = total_estimation
        rpo_data['annual']['contract_reel'] = total_contract
        rpo_data['annual']['dollar_reel'] = total_dollar
        rpo_data['annual']['hr_pap_reel'] = total_hr_pap
        rpo_data['annual']['hr_pap_reel_sans_week1'] = total_hr_pap_sans_week1

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

        # Calculer le taux marketing réel (estimation / hr_pap = estimations par heure)
        if total_hr_pap > 0:
            rpo_data['annual']['mktg_reel'] = round(total_estimation / total_hr_pap, 2)
        else:
            rpo_data['annual']['mktg_reel'] = 0

        # Calculer le prod_horaire moyen depuis les semaines de mai à septembre (mois 4-8)
        total_prod_horaire = 0
        nb_semaines_prod_horaire = 0
        for month_idx in range(4, 9):  # Mai (4) à Septembre (8)
            month_key = str(month_idx)
            if month_key in rpo_data['weekly']:
                for week_number in range(1, 6):
                    week_key = str(week_number)
                    if week_key in rpo_data['weekly'][month_key]:
                        prod_h = rpo_data['weekly'][month_key][week_key].get('prod_horaire', '-')
                        if prod_h not in ['-', '', None, 0]:
                            try:
                                total_prod_horaire += float(prod_h)
                                nb_semaines_prod_horaire += 1
                            except (ValueError, TypeError):
                                pass

        # Moyenne des prod_horaire
        if nb_semaines_prod_horaire > 0:
            rpo_data['annual']['prod_horaire'] = round(total_prod_horaire / nb_semaines_prod_horaire, 2)
        else:
            rpo_data['annual']['prod_horaire'] = 0

        print(f"[SYNC] [RPO SYNC] Totaux annuels agregés:", flush=True)
        print(f"  - H de PÀP: {total_hr_pap}h (sans week1: {total_hr_pap_sans_week1}h)", flush=True)
        print(f"  - Estimations: {total_estimation}", flush=True)
        print(f"  - Contracts: {total_contract}", flush=True)
        print(f"  - Dollars: {total_dollar}", flush=True)
        print(f"  - Taux vente: {rpo_data['annual']['vente_reel']}%", flush=True)
        print(f"  - Contrat moyen: {rpo_data['annual']['moyen_reel']}$", flush=True)
        print(f"  - Prod horaire: {rpo_data['annual']['prod_horaire']}$/h ({nb_semaines_prod_horaire} semaines)", flush=True)

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
        print(f"[DEBUG SAVE] AVANT save - annual.contract_reel = {rpo_data['annual'].get('contract_reel')}", flush=True)
        print(f"[DEBUG SAVE] AVANT save - annual.dollar_reel = {rpo_data['annual'].get('dollar_reel')}", flush=True)
        save_user_rpo_data(username, rpo_data)

        # Vérifier immédiatement après save
        import json as json_verify
        filepath_verify = get_user_rpo_file(username)
        with open(filepath_verify, 'r', encoding='utf-8') as f_verify:
            saved_data = json_verify.load(f_verify)
        print(f"[DEBUG SAVE] APRES save (relecture) - annual.contract_reel = {saved_data['annual'].get('contract_reel')}", flush=True)
        print(f"[DEBUG SAVE] APRES save (relecture) - annual.dollar_reel = {saved_data['annual'].get('dollar_reel')}", flush=True)

        print(f"[OK] [RPO SYNC] Synchronisation soumissions -> RPO reussie pour {username}", flush=True)

        # Libérer le lock AVANT les opérations secondaires (badges, coach sync)
        _sync_lock_ctx.__exit__(None, None, None)
        _lock_held = False

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
    finally:
        # S'assurer que le lock est libéré même en cas d'exception
        if _lock_held:
            try:
                _sync_lock_ctx.__exit__(None, None, None)
            except:
                pass


# ========================================
# ÉTATS DES RÉSULTATS
# ========================================

def update_etats_resultats_budget(username: str, budget_percent_data: Dict[str, float]) -> bool:
    """
    Met à jour les pourcentages Budget des États des Résultats
    budget_percent_data: dictionnaire {category: percent}
    """
    with rpo_file_lock(username):
        rpo_data = load_user_rpo_data(username)

        if 'etats_resultats' not in rpo_data:
            rpo_data['etats_resultats'] = {}

        rpo_data['etats_resultats']['budget_percent'] = budget_percent_data
        return save_user_rpo_data(username, rpo_data)


def get_etats_resultats_budget(username: str) -> Dict[str, float]:
    """Récupère les pourcentages Budget des États des Résultats"""
    rpo_data = load_user_rpo_data(username)
    return rpo_data.get('etats_resultats', {}).get('budget_percent', {})


def update_etats_resultats_cible_percent(username: str, cible_percent: Dict[str, float]) -> bool:
    """
    Sauvegarde uniquement les % ciblés des États des Résultats
    Les $ ciblés sont calculés dynamiquement: CA × % cible
    cible_percent: dictionnaire {category: pourcentage}

    NOTE: Utilise 'cible_percent' séparé de 'budget_percent' pour éviter les conflits
    """
    if cible_percent is None or len(cible_percent) == 0:
        # Ne pas écraser avec des données vides
        return True

    with rpo_file_lock(username):
        rpo_data = load_user_rpo_data(username)

        if 'etats_resultats' not in rpo_data:
            rpo_data['etats_resultats'] = {}

        rpo_data['etats_resultats']['cible_percent'] = cible_percent
        return save_user_rpo_data(username, rpo_data)


def get_etats_resultats_actuel(username: str) -> Dict[str, Any]:
    """Récupère les % ciblés des États des Résultats
    Les $ ciblés sont calculés dynamiquement: CA × % cible

    NOTE: Lit depuis 'cible_percent' (nouveau champ séparé de 'budget_percent')
    """
    rpo_data = load_user_rpo_data(username)
    etats_resultats = rpo_data.get('etats_resultats', {})

    # Lire depuis 'cible_percent' (nouveau) ou fallback vers 'budget_percent' (ancien)
    cible_percent = etats_resultats.get('cible_percent', {})
    if not cible_percent:
        # Fallback pour données existantes qui utilisaient budget_percent
        cible_percent = etats_resultats.get('budget_percent', {})

    print(f"[DEBUG GET ÉTATS] cible_percent has {len(cible_percent)} categories", flush=True)
    return {
        'budget_percent': cible_percent  # Retourne sous le nom attendu par le frontend
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

    # Lock couvre le cycle complet load -> modify -> save
    with rpo_file_lock(username):

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
