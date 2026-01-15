"""
Script de migration pour mettre a jour les coaches au nouveau format JSON
- Supprime la section annual
- Garde weekly avec les bonnes semaines
- Garde coach_previsions et entrepreneurs_metrics
Usage: python migration_coaches.py
"""

import sys
import os
import json
from pathlib import Path
sys.path.insert(0, '.')

import sqlite3
from database import get_database_path
from QE.Backend.rpo import (
    load_user_rpo_data,
    save_user_rpo_data
)

# Structure des semaines valides par mois (2026)
# 4 semaines: Jan, Fev, Avr, Mai, Juil, Sept, Oct, Dec
# 5 semaines: Mars, Juin, Aout, Nov
VALID_WEEKS_PER_MONTH = {
    "0": ["1", "2", "3", "4"],       # Janvier
    "1": ["1", "2", "3", "4"],       # Fevrier
    "2": ["1", "2", "3", "4", "5"],  # Mars
    "3": ["1", "2", "3", "4"],       # Avril
    "4": ["1", "2", "3", "4"],       # Mai
    "5": ["1", "2", "3", "4", "5"],  # Juin
    "6": ["1", "2", "3", "4"],       # Juillet
    "7": ["1", "2", "3", "4", "5"],  # Aout
    "8": ["1", "2", "3", "4"],       # Septembre
    "9": ["1", "2", "3", "4"],       # Octobre
    "10": ["1", "2", "3", "4", "5"], # Novembre
    "11": ["1", "2", "3", "4"],      # Decembre
}

# Champs a garder dans weekly pour coach
COACH_WEEK_FIELDS = ["week_label", "h_marketing", "estimation", "contract", "dollar", "produit"]

# Labels des semaines 2026
WEEK_LABELS = {
    "0": {"1": "5 - 11 janv", "2": "12 - 18 janv", "3": "19 - 25 janv", "4": "26 janv - 1 févr"},
    "1": {"1": "2 - 8 févr", "2": "9 - 15 févr", "3": "16 - 22 févr", "4": "23 févr - 1 mars"},
    "2": {"1": "2 - 8 mars", "2": "9 - 15 mars", "3": "16 - 22 mars", "4": "23 - 29 mars", "5": "30 mars - 5 avr"},
    "3": {"1": "6 - 12 avr", "2": "13 - 19 avr", "3": "20 - 26 avr", "4": "27 avr - 3 mai"},
    "4": {"1": "4 - 10 mai", "2": "11 - 17 mai", "3": "18 - 24 mai", "4": "25 - 31 mai"},
    "5": {"1": "1 - 7 juin", "2": "8 - 14 juin", "3": "15 - 21 juin", "4": "22 - 28 juin", "5": "29 juin - 5 juil"},
    "6": {"1": "6 - 12 juil", "2": "13 - 19 juil", "3": "20 - 26 juil", "4": "27 juil - 2 août"},
    "7": {"1": "3 - 9 août", "2": "10 - 16 août", "3": "17 - 23 août", "4": "24 - 30 août", "5": "31 août - 6 sept"},
    "8": {"1": "7 - 13 sept", "2": "14 - 20 sept", "3": "21 - 27 sept", "4": "28 sept - 4 oct"},
    "9": {"1": "5 - 11 oct", "2": "12 - 18 oct", "3": "19 - 25 oct", "4": "26 oct - 1 nov"},
    "10": {"1": "2 - 8 nov", "2": "9 - 15 nov", "3": "16 - 22 nov", "4": "23 - 29 nov", "5": "30 nov - 6 déc"},
    "11": {"1": "7 - 13 déc", "2": "14 - 20 déc", "3": "21 - 27 déc", "4": "28 déc - 3 janv"},
}

# Valeurs par defaut pour une semaine coach
DEFAULT_COACH_WEEK = {
    "week_label": "",
    "h_marketing": 0,
    "estimation": 0,
    "contract": 0,
    "dollar": 0,
    "produit": 0
}


def migrate_coach_rpo(username: str):
    """
    Migration complete pour un coach:
    1. Supprime la section annual
    2. Nettoie weekly (garde seulement les bonnes semaines et champs)
    3. Preserve coach_previsions et entrepreneurs_metrics
    TOUT EN UNE SEULE SAUVEGARDE
    """
    try:
        rpo_data = load_user_rpo_data(username)
        modified = False
        weeks_removed = 0
        fields_cleaned = 0

        # 1. Supprimer la section annual
        if 'annual' in rpo_data:
            del rpo_data['annual']
            modified = True
            print(f"    [CLEAN] Supprime section annual", flush=True)

        # 2. Supprimer etats_resultats si present (pas pour coach)
        if 'etats_resultats' in rpo_data:
            del rpo_data['etats_resultats']
            modified = True
            print(f"    [CLEAN] Supprime section etats_resultats", flush=True)

        # 3. Supprimer monthly si present (pas pour coach)
        if 'monthly' in rpo_data:
            del rpo_data['monthly']
            modified = True
            print(f"    [CLEAN] Supprime section monthly", flush=True)

        # 3. Agreger les donnees weekly de tous les entrepreneurs du coach
        entrepreneurs_for_coach = get_entrepreneurs_for_coach(username)
        aggregated_weekly = aggregate_entrepreneurs_weekly(entrepreneurs_for_coach)
        if aggregated_weekly:
            print(f"    [AGGREGATE] Donnees de {len(entrepreneurs_for_coach)} entrepreneurs agregees", flush=True)

        # 4. Nettoyer weekly
        if 'weekly' not in rpo_data:
            rpo_data['weekly'] = {}
            modified = True

        # Supprimer mois invalides (-2, -1, etc.)
        for month_key in list(rpo_data['weekly'].keys()):
            try:
                month_idx = int(month_key)
                if month_idx < 0 or month_idx > 11:
                    del rpo_data['weekly'][month_key]
                    modified = True
                    print(f"    [CLEAN] Supprime mois invalide {month_key}", flush=True)
            except:
                del rpo_data['weekly'][month_key]
                modified = True

        # Pour chaque mois valide
        for month_key in list(VALID_WEEKS_PER_MONTH.keys()):
            valid_weeks = VALID_WEEKS_PER_MONTH[month_key]

            if month_key not in rpo_data['weekly']:
                rpo_data['weekly'][month_key] = {}
                modified = True

            month_data = rpo_data['weekly'][month_key]

            # Supprimer semaines invalides
            for week_key in list(month_data.keys()):
                if week_key not in valid_weeks:
                    del month_data[week_key]
                    weeks_removed += 1
                    modified = True
                    print(f"    [CLEAN] Supprime semaine {month_key}/{week_key}", flush=True)

            # S'assurer que toutes les semaines valides existent avec les bons champs
            for week_key in valid_weeks:
                week_label = WEEK_LABELS.get(month_key, {}).get(week_key, "")

                # Creer la semaine avec les totaux des entrepreneurs
                month_data[week_key] = {
                    "week_label": week_label,
                    "h_marketing": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("h_marketing", 0),
                    "estimation": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("estimation", 0),
                    "contract": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("contract", 0),
                    "dollar": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("dollar", 0),
                    "produit": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("produit", 0)
                }
                modified = True

        # 4. Charger coach_previsions depuis l'ancien fichier _metrics.json si existe
        old_metrics = load_old_coach_metrics(username)
        old_previsions = load_old_coach_previsions(username)

        if 'coach_previsions' not in rpo_data:
            rpo_data['coach_previsions'] = {}

        # Migrer les valeurs depuis _metrics.json
        if old_metrics:
            rpo_data['coach_previsions']['cm'] = old_metrics.get('cm', 2500)
            rpo_data['coach_previsions']['ratioMktg'] = old_metrics.get('ratioMktg', 85)
            rpo_data['coach_previsions']['tauxVente'] = old_metrics.get('tauxVente', 30)
            modified = True
            print(f"    [MIGRATE] coach_previsions depuis _metrics.json (cm={old_metrics.get('cm')}, ratio={old_metrics.get('ratioMktg')}, taux={old_metrics.get('tauxVente')})", flush=True)
        else:
            # Valeurs par defaut si pas d'ancien fichier
            if 'cm' not in rpo_data['coach_previsions']:
                rpo_data['coach_previsions']['cm'] = 2500
            if 'ratioMktg' not in rpo_data['coach_previsions']:
                rpo_data['coach_previsions']['ratioMktg'] = 85
            if 'tauxVente' not in rpo_data['coach_previsions']:
                rpo_data['coach_previsions']['tauxVente'] = 30

        # Migrer totalObjectif depuis _previsions.json
        if old_previsions:
            total = sum(float(v) for v in old_previsions.values())
            rpo_data['coach_previsions']['totalObjectif'] = total
            modified = True
            print(f"    [MIGRATE] totalObjectif depuis _previsions.json ({total})", flush=True)
        elif 'totalObjectif' not in rpo_data['coach_previsions']:
            rpo_data['coach_previsions']['totalObjectif'] = 0
            modified = True

        # 5. Peupler entrepreneurs_metrics depuis la BD
        entrepreneurs_for_coach = get_entrepreneurs_for_coach(username)
        if entrepreneurs_for_coach:
            if 'entrepreneurs_metrics' not in rpo_data:
                rpo_data['entrepreneurs_metrics'] = {}

            for ent_username in entrepreneurs_for_coach:
                if ent_username not in rpo_data['entrepreneurs_metrics']:
                    # Charger les donnees de l'entrepreneur pour obtenir objectif_ca
                    ent_data = load_user_rpo_data(ent_username)
                    objectif_ca = ent_data.get('annual', {}).get('objectif_ca', 0)

                    rpo_data['entrepreneurs_metrics'][ent_username] = {
                        "objectif_ca": objectif_ca,
                        "cm": 2500,
                        "ratioMktg": 85,
                        "tauxVente": 30
                    }
                    modified = True
                    print(f"    [ADD] Ajoute {ent_username} dans entrepreneurs_metrics", flush=True)
        elif 'entrepreneurs_metrics' not in rpo_data:
            rpo_data['entrepreneurs_metrics'] = {}
            modified = True

        # SAUVEGARDE UNIQUE
        if modified:
            save_user_rpo_data(username, rpo_data)
            status_parts = []
            if weeks_removed > 0:
                status_parts.append(f"-{weeks_removed} sem")
            if fields_cleaned > 0:
                status_parts.append(f"-{fields_cleaned} champs")
            return True, " ".join(status_parts) if status_parts else "OK"
        else:
            return True, "deja OK"

    except Exception as e:
        print(f"[ERROR] Migration {username}: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def aggregate_entrepreneurs_weekly(entrepreneurs: list):
    """
    Agregue les donnees weekly de tous les entrepreneurs
    Retourne un dict {month: {week: {h_marketing, estimation, contract, dollar, produit}}}
    """
    aggregated = {}

    for ent_username in entrepreneurs:
        try:
            ent_data = load_user_rpo_data(ent_username)
            ent_weekly = ent_data.get('weekly', {})

            for month_key, month_data in ent_weekly.items():
                if month_key not in aggregated:
                    aggregated[month_key] = {}

                for week_key, week_data in month_data.items():
                    if week_key not in aggregated[month_key]:
                        aggregated[month_key][week_key] = {
                            "h_marketing": 0,
                            "estimation": 0,
                            "contract": 0,
                            "dollar": 0,
                            "produit": 0
                        }

                    # Ajouter les valeurs (convertir en float si necessaire)
                    for field in ["h_marketing", "estimation", "contract", "dollar", "produit"]:
                        value = week_data.get(field, 0)
                        # Gerer les valeurs "-" ou vides
                        if value == "-" or value == "" or value is None:
                            value = 0
                        try:
                            aggregated[month_key][week_key][field] += float(value)
                        except (ValueError, TypeError):
                            pass

        except Exception as e:
            print(f"    [WARN] Erreur agregation {ent_username}: {e}")

    return aggregated


def load_old_coach_metrics(coach_username: str):
    """Charge les anciennes metriques depuis _metrics.json"""
    if sys.platform == 'win32':
        base_dir = Path(__file__).parent / "data" / "coach_previsions"
    else:
        base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
        base_dir = Path(base_cloud) / "coach_previsions"

    file_path = base_dir / f"{coach_username}_metrics.json"

    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('metrics', {})
    except Exception as e:
        print(f"    [WARN] Impossible de lire {file_path}: {e}")
        return None


def load_old_coach_previsions(coach_username: str):
    """Charge les anciennes previsions depuis _previsions.json"""
    if sys.platform == 'win32':
        base_dir = Path(__file__).parent / "data" / "coach_previsions"
    else:
        base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
        base_dir = Path(base_cloud) / "coach_previsions"

    file_path = base_dir / f"{coach_username}_previsions.json"

    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('previsions', {})
    except Exception as e:
        print(f"    [WARN] Impossible de lire {file_path}: {e}")
        return None


def get_all_coaches():
    """Recupere tous les coaches actifs"""
    DB_PATH = get_database_path()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role='coach' AND is_active=1")
        coaches = [row[0] for row in cursor.fetchall()]

    return coaches


def get_entrepreneurs_for_coach(coach_username: str):
    """Recupere tous les entrepreneurs assignes a un coach"""
    DB_PATH = get_database_path()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username FROM users WHERE role='entrepreneur' AND is_active=1 AND assigned_coach=?",
            (coach_username,)
        )
        entrepreneurs = [row[0] for row in cursor.fetchall()]

    return entrepreneurs


def main():
    print("=" * 80)
    print("MIGRATION COACHES - NOUVEAU FORMAT JSON")
    print("=" * 80)
    print()
    print("Structure cible:")
    print("  - weekly (52 semaines avec h_marketing, estimation, contract, dollar, produit)")
    print("  - coach_previsions")
    print("  - entrepreneurs_metrics")
    print("  - last_updated")
    print()

    # 1. Recuperer tous les coaches
    print("[ETAPE 1/2] Recuperation des coaches...")
    coaches = get_all_coaches()
    print(f"  OK {len(coaches)} coaches trouves")
    print()

    # 2. Migration complete
    print("[ETAPE 2/2] Migration complete...")
    print("  - Supprime: section annual, monthly, etats_resultats")
    print("  - Supprime: semaines invalides (sem 5 pour mois a 4 sem)")
    print("  - Supprime: champs inutiles (rating, commentaire, etc.)")
    print("  - Garde: week_label, h_marketing, estimation, contract, dollar, produit")
    print()

    success_count = 0
    already_ok = 0
    for i, username in enumerate(coaches, 1):
        print(f"  [{i}/{len(coaches)}] {username}...", end=" ")
        try:
            success, status = migrate_coach_rpo(username)
            if success:
                if "deja OK" in status:
                    print("(deja OK)")
                    already_ok += 1
                else:
                    print(f"OK ({status})")
                success_count += 1
            else:
                print(f"ERREUR: {status}")
        except Exception as e:
            print(f"ERREUR ({e})")

    print(f"  => {success_count}/{len(coaches)} OK ({already_ok} deja OK)")
    print()

    # Resume
    print("=" * 80)
    print("MIGRATION TERMINEE")
    print("=" * 80)
    print()
    print(f"RESUME: {len(coaches)} coaches traites ({already_ok} deja OK)")
    print()
    print("STRUCTURE FINALE:")
    print("  [OK] weekly (52 semaines)")
    print("  [OK] coach_previsions")
    print("  [OK] entrepreneurs_metrics")
    print("  [OK] last_updated")
    print()
    print("CHAMPS PAR SEMAINE:")
    print("  h_marketing, estimation, contract, dollar, produit")
    print()
    print("JSON au nouveau format!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[ANNULE] Migration interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERREUR FATALE] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
