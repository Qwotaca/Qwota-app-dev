"""
Script de migration pour mettre a jour la direction au nouveau format JSON
- UN SEUL FICHIER pour tous les users direction
- Agrege les donnees de tous les coaches
Usage: python migration_direction.py
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
VALID_WEEKS_PER_MONTH = {
    "0": ["1", "2", "3", "4"],
    "1": ["1", "2", "3", "4"],
    "2": ["1", "2", "3", "4", "5"],
    "3": ["1", "2", "3", "4"],
    "4": ["1", "2", "3", "4"],
    "5": ["1", "2", "3", "4", "5"],
    "6": ["1", "2", "3", "4"],
    "7": ["1", "2", "3", "4", "5"],
    "8": ["1", "2", "3", "4"],
    "9": ["1", "2", "3", "4"],
    "10": ["1", "2", "3", "4", "5"],
    "11": ["1", "2", "3", "4"],
}

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

# Champs par semaine pour direction
DIRECTION_WEEK_FIELDS = ["week_label", "h_marketing", "estimation", "contract", "dollar", "produit"]

DEFAULT_DIRECTION_WEEK = {
    "week_label": "",
    "h_marketing": 0,
    "estimation": 0,
    "contract": 0,
    "dollar": 0,
    "produit": 0
}


def get_all_coaches():
    """Recupere tous les coaches actifs"""
    DB_PATH = get_database_path()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role='coach' AND is_active=1")
        return [row[0] for row in cursor.fetchall()]


def aggregate_coaches_weekly(coaches: list):
    """
    Agregue les donnees weekly de tous les coaches
    Retourne un dict {month: {week: {h_marketing, estimation, contract, dollar, produit}}}
    """
    aggregated = {}

    for coach_username in coaches:
        try:
            coach_data = load_user_rpo_data(coach_username)
            coach_weekly = coach_data.get('weekly', {})

            for month_key, month_data in coach_weekly.items():
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

                    for field in ["h_marketing", "estimation", "contract", "dollar", "produit"]:
                        value = week_data.get(field, 0)
                        if value == "-" or value == "" or value is None:
                            value = 0
                        try:
                            aggregated[month_key][week_key][field] += float(value)
                        except (ValueError, TypeError):
                            pass

        except Exception as e:
            print(f"    [WARN] Erreur agregation coach {coach_username}: {e}")

    return aggregated


def load_old_direction_metrics():
    """Charge les anciennes metriques direction depuis shared_direction_metrics.json"""
    if sys.platform == 'win32':
        base_dir = Path(__file__).parent / "data" / "direction_previsions"
    else:
        base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
        base_dir = Path(base_cloud) / "direction_previsions"

    file_path = base_dir / "shared_direction_metrics.json"
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('metrics', {})
        except:
            pass
    return None


def load_old_direction_previsions():
    """Charge les anciennes previsions direction depuis shared_direction_previsions.json"""
    if sys.platform == 'win32':
        base_dir = Path(__file__).parent / "data" / "direction_previsions"
    else:
        base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
        base_dir = Path(base_cloud) / "direction_previsions"

    file_path = base_dir / "shared_direction_previsions.json"
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('previsions', {})
        except:
            pass
    return None


def migrate_direction_rpo():
    """
    Migration complete pour la direction:
    1. Charge le fichier direction_rpo.json existant
    2. Supprime annual, monthly, etats_resultats
    3. Agregue les donnees de tous les coaches
    4. Cree coaches_metrics et direction_previsions
    """
    try:
        # Charger le fichier direction existant
        rpo_data = load_user_rpo_data("direction")
        modified = False

        # 1. Supprimer les sections inutiles
        for section in ['annual', 'monthly', 'etats_resultats']:
            if section in rpo_data:
                del rpo_data[section]
                modified = True
                print(f"    [CLEAN] Supprime section {section}", flush=True)

        # 2. Recuperer tous les coaches et agreger leurs donnees
        coaches = get_all_coaches()
        aggregated_weekly = aggregate_coaches_weekly(coaches)
        print(f"    [AGGREGATE] Donnees de {len(coaches)} coaches agregees", flush=True)

        # 3. Construire le weekly avec les bonnes semaines
        rpo_data['weekly'] = {}

        for month_key, valid_weeks in VALID_WEEKS_PER_MONTH.items():
            rpo_data['weekly'][month_key] = {}

            for week_key in valid_weeks:
                week_label = WEEK_LABELS.get(month_key, {}).get(week_key, "")
                rpo_data['weekly'][month_key][week_key] = {
                    "week_label": week_label,
                    "h_marketing": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("h_marketing", 0),
                    "estimation": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("estimation", 0),
                    "contract": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("contract", 0),
                    "dollar": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("dollar", 0),
                    "produit": aggregated_weekly.get(month_key, {}).get(week_key, {}).get("produit", 0)
                }

        modified = True

        # 4. Charger les anciennes donnees direction
        old_direction_metrics = load_old_direction_metrics()
        old_direction_previsions = load_old_direction_previsions()

        # 5. Creer direction_previsions
        if 'direction_previsions' not in rpo_data:
            rpo_data['direction_previsions'] = {}

        # Importer les metriques depuis shared_direction_metrics.json
        if old_direction_metrics:
            rpo_data['direction_previsions']['cm'] = old_direction_metrics.get('cm', 2500)
            rpo_data['direction_previsions']['ratioMktg'] = old_direction_metrics.get('ratioMktg', 85)
            rpo_data['direction_previsions']['tauxVente'] = old_direction_metrics.get('tauxVente', 30)
            print(f"    [MIGRATE] direction_previsions depuis shared_direction_metrics.json", flush=True)
        else:
            rpo_data['direction_previsions']['cm'] = 2500
            rpo_data['direction_previsions']['ratioMktg'] = 85
            rpo_data['direction_previsions']['tauxVente'] = 30

        # Calculer totalObjectif depuis les previsions par coach
        if old_direction_previsions:
            total_objectif = sum(float(v) for v in old_direction_previsions.values())
            print(f"    [MIGRATE] totalObjectif depuis shared_direction_previsions.json = {total_objectif}", flush=True)
        else:
            # Sinon calculer depuis les coaches
            total_objectif = 0
            for coach_username in coaches:
                try:
                    coach_data = load_user_rpo_data(coach_username)
                    total_objectif += coach_data.get('coach_previsions', {}).get('totalObjectif', 0)
                except:
                    pass
            print(f"    [CALC] totalObjectif depuis coaches = {total_objectif}", flush=True)

        rpo_data['direction_previsions']['totalObjectif'] = total_objectif

        # Supprimer l'ancien coach_previsions
        if 'coach_previsions' in rpo_data:
            del rpo_data['coach_previsions']
            modified = True

        # 6. Creer coaches_metrics avec objectifs depuis direction_previsions
        rpo_data['coaches_metrics'] = {}
        for coach_username in coaches:
            try:
                coach_data = load_user_rpo_data(coach_username)
                coach_prev = coach_data.get('coach_previsions', {})

                # L'objectif vient de direction (shared_direction_previsions) ou du coach
                objectif_from_direction = 0
                if old_direction_previsions and coach_username in old_direction_previsions:
                    objectif_from_direction = old_direction_previsions[coach_username]

                rpo_data['coaches_metrics'][coach_username] = {
                    "totalObjectif": objectif_from_direction if objectif_from_direction else coach_prev.get('totalObjectif', 0),
                    "cm": coach_prev.get('cm', 2500),
                    "ratioMktg": coach_prev.get('ratioMktg', 85),
                    "tauxVente": coach_prev.get('tauxVente', 30)
                }
                print(f"    [ADD] {coach_username} dans coaches_metrics (objectif={rpo_data['coaches_metrics'][coach_username]['totalObjectif']})", flush=True)
            except Exception as e:
                print(f"    [WARN] Erreur {coach_username}: {e}")

        # Supprimer l'ancien entrepreneurs_metrics si present
        if 'entrepreneurs_metrics' in rpo_data:
            del rpo_data['entrepreneurs_metrics']
            modified = True

        # SAUVEGARDE
        save_user_rpo_data("direction", rpo_data)
        return True, "OK"

    except Exception as e:
        print(f"[ERROR] Migration direction: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)


def main():
    print("=" * 80)
    print("MIGRATION DIRECTION - NOUVEAU FORMAT JSON")
    print("=" * 80)
    print()
    print("Structure cible:")
    print("  - weekly (52 semaines agregees de tous les coaches)")
    print("  - direction_previsions (cm, ratioMktg, tauxVente, totalObjectif)")
    print("  - coaches_metrics (metriques par coach)")
    print("  - last_updated")
    print()
    print("NOTE: UN SEUL fichier direction_rpo.json pour tous les users direction")
    print()

    print("[MIGRATION] direction_rpo.json...")
    success, status = migrate_direction_rpo()

    if success:
        print(f"  => OK ({status})")
    else:
        print(f"  => ERREUR: {status}")

    print()
    print("=" * 80)
    print("MIGRATION TERMINEE")
    print("=" * 80)
    print()
    print("STRUCTURE FINALE:")
    print("  [OK] weekly (52 semaines)")
    print("  [OK] direction_previsions")
    print("  [OK] coaches_metrics")
    print("  [OK] last_updated")
    print()
    print("JSON au nouveau format!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[ANNULE] Migration interrompue")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERREUR FATALE] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
