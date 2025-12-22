"""
Backend routes pour RPO (Résultats, Prévisions, Objectifs)
Gère les données annuelles, mensuelles et hebdomadaires par utilisateur
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

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
    rpo_data = load_user_rpo_data(username)

    if 'weekly' not in rpo_data:
        rpo_data['weekly'] = {}

    month_key = str(month_index)
    if month_key not in rpo_data['weekly']:
        rpo_data['weekly'][month_key] = {}

    week_key = str(week_number)
    rpo_data['weekly'][month_key][week_key] = weekly_data

    return save_user_rpo_data(username, rpo_data)


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
            month_index = date.month - 1  # 0-11 pour janvier-décembre 2026

            # Trouver le premier lundi du mois (avec timezone de Toronto)
            first_day = datetime(date.year, date.month, 1, tzinfo=TORONTO_TZ)
            if first_day.weekday() == 0:  # Si le 1er est déjà un lundi
                first_monday = first_day
            else:
                days_until_monday = 7 - first_day.weekday()
                first_monday = first_day + timedelta(days=days_until_monday)

            # Déterminer dans quelle semaine du mois tombe cette date
            # basé sur le jeudi (ISO 8601: la semaine appartient au mois qui contient le jeudi)
            thursday_of_week = date + timedelta(days=(3 - date.weekday()))

            # Compter les lundis depuis le début du mois jusqu'à cette date
            if date < first_monday:
                week_number = 1  # Avant le premier lundi = semaine 1
            else:
                days_since_first_monday = (date - first_monday).days
                week_number = (days_since_first_monday // 7) + 1

        else:
            # Default: dates hors période fiscale (décembre 2025 - décembre 2026)
            month_index = 0  # Default janvier 2026
            week_number = 1

        return (month_index, week_number)
    except Exception as e:
        print(f"Erreur parsing date {date_str}: {e}")
        return (0, 1)  # Default janvier 2026 semaine 1


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

                # Initialiser commentaire et rating s'ils n'existent pas
                if 'commentaire' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['commentaire'] = 'Problème: - | Focus: -'
                if 'rating' not in rpo_data['weekly'][month_key][week_key]:
                    rpo_data['weekly'][month_key][week_key]['rating'] = 0

                # Réinitialiser le reste
                rpo_data['weekly'][month_key][week_key]['estimation'] = 0
                rpo_data['weekly'][month_key][week_key]['contract'] = 0
                rpo_data['weekly'][month_key][week_key]['dollar'] = 0

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

        # 2. Lire soumissions_signees (Contrat réel + $ réel)
        soumissions_signees_path = os.path.join(base_cloud, "soumissions_signees", username, "soumissions.json")
        if os.path.exists(soumissions_signees_path):
            with open(soumissions_signees_path, 'r', encoding='utf-8') as f:
                soumissions_signees = json.load(f)

            print(f"[INFO] [RPO SYNC] {len(soumissions_signees)} soumissions signees trouvees pour {username}", flush=True)

            for soumission in soumissions_signees:
                date_str = soumission.get('date', '')
                prix_str = soumission.get('prix', '0')

                # Parser le prix (format: "1 000,00 $" ou "1 500,00 $" ou "1000")
                # Étape 1: Retirer tous les espaces (normaux et non-breakable), $, et remplacer , par .
                import re
                prix_clean = re.sub(r'\s+', '', prix_str)  # Retire tous les espaces (normaux + \xa0)
                prix_clean = prix_clean.replace('$', '').replace(',', '.')
                try:
                    prix = float(prix_clean)
                    print(f"  [PRIX] [RPO SYNC] Prix parsé: {prix_str} → {prix}", flush=True)
                except Exception as e:
                    print(f"  [ERREUR PRIX] [RPO SYNC] Impossible de parser '{prix_str}': {e}", flush=True)
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

        # 3. Agréger les données hebdomadaires vers les totaux annuels
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

        # Calculer prod_horaire automatiquement pour chaque semaine: $ / H marketing
        print(f"[SYNC] [RPO SYNC] Calcul prod_horaire automatique...", flush=True)
        for month_idx in all_months:
            month_key = str(month_idx)
            if month_key in rpo_data['weekly']:
                for week_number in range(1, 6):
                    week_key = str(week_number)
                    if week_key in rpo_data['weekly'][month_key]:
                        week_data = rpo_data['weekly'][month_key][week_key]
                        h_marketing = week_data.get('h_marketing', '-')
                        dollar = week_data.get('dollar', 0)

                        # Calculer prod_horaire seulement si h_marketing est un nombre valide et > 0
                        if h_marketing not in ['-', '', None] and dollar > 0:
                            try:
                                h_marketing_float = float(h_marketing)
                                if h_marketing_float > 0:
                                    prod_horaire = round(dollar / h_marketing_float, 2)
                                    rpo_data['weekly'][month_key][week_key]['prod_horaire'] = prod_horaire
                                else:
                                    rpo_data['weekly'][month_key][week_key]['prod_horaire'] = 0
                            except (ValueError, TypeError):
                                rpo_data['weekly'][month_key][week_key]['prod_horaire'] = 0
                        else:
                            rpo_data['weekly'][month_key][week_key]['prod_horaire'] = 0

        # Sauvegarder les données RPO mises à jour
        save_user_rpo_data(username, rpo_data)
        print(f"[OK] [RPO SYNC] Synchronisation soumissions -> RPO reussie pour {username}", flush=True)
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


def update_etats_resultats_actuel(username: str, actuel_data: Dict[str, float], cible_data: Dict[str, float] = None) -> bool:
    """
    Met à jour les montants Actuel et CIBLÉ des États des Résultats
    actuel_data: dictionnaire {category: montant}
    cible_data: dictionnaire {category: montant} (optionnel)
    """
    rpo_data = load_user_rpo_data(username)

    if 'etats_resultats' not in rpo_data:
        rpo_data['etats_resultats'] = {}

    rpo_data['etats_resultats']['actuel'] = actuel_data

    # Sauvegarder aussi les données CIBLÉ si fournies
    if cible_data is not None:
        rpo_data['etats_resultats']['cible'] = cible_data

    return save_user_rpo_data(username, rpo_data)


def get_etats_resultats_actuel(username: str) -> Dict[str, Any]:
    """Récupère les montants Actuel et CIBLÉ des États des Résultats"""
    rpo_data = load_user_rpo_data(username)
    etats_resultats = rpo_data.get('etats_resultats', {})
    return {
        'actuel': etats_resultats.get('actuel', {}),
        'cible': etats_resultats.get('cible', {})
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

    # Initialiser les montants par semaine
    week_dollars = {}
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
            if week_index not in week_dollars:
                week_dollars[week_index] = 0
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

            # Mettre à jour le montant dollar si on a des ventes pour cette semaine
            if week_counter in week_dollars:
                rpo_data['weekly'][month_key][week_key]['dollar'] = week_dollars[week_counter]

            week_counter += 1

    # Sauvegarder le RPO mis à jour
    save_success = save_user_rpo_data(username, rpo_data)

    return {
        "status": "success" if save_success else "error",
        "ventes_synced": ventes_synced,
        "weeks_updated": len(week_dollars),
        "total_montant": sum(week_dollars.values())
    }
