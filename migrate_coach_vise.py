"""
Script de migration pour ajouter les champs *_vise aux RPO des coaches
Calcule les objectifs hebdomadaires à partir du plan d'affaires du coach
(100% identique au flux entrepreneur)
"""

import json
import sqlite3
import sys
from pathlib import Path

# Chemins
DATA_DIR = Path(__file__).parent / "data"
RPO_DIR = DATA_DIR / "rpo"
USERS_DB = DATA_DIR / "qwota.db"

# Pattern de pourcentages par semaine (52 semaines) - IDENTIQUE à l'entrepreneur
PERCENTAGE_PATTERN = [
    0,      # Index 0: 5-11 janv 2026 (semaine vide)
    0.5, 2.0, 2.0,  # Index 1-3: 12 janv - 1 fév
    3.0, 2.5, 3.0, 3.0,  # Index 4-7: 2 fév - 1 mars
    3.5, 4.0, 4.5, 5.5,  # Index 8-11: 2 mars - 29 mars
    4.5, 6.5, 5.5, 6.0, 6.0,  # Index 12-16: 30 mars - 4 mai
    4.5, 4.5, 4.5, 4.5,  # Index 17-20: 5 mai - 1 juin
    3.5, 4.0, 3.5, 3.0,  # Index 21-24: 2 juin - 29 juin
    3.0, 3.0, 3.0, 2.0, 1.0,  # Index 25-29: 30 juin - 3 août
    1.0, 1.0, 1.0, 1.0,  # Index 30-33: 4 août - 31 août
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0  # Index 34-51: reste (0%)
]

# Mapping semaine globale vers (mois, semaine dans le mois) - IDENTIQUE à l'entrepreneur
WEEK_OFFSETS = {
    0: 0,    # Janvier 2026
    1: 5,    # Février 2026
    2: 9,    # Mars 2026
    3: 13,   # Avril 2026
    4: 18,   # Mai 2026
    5: 22,   # Juin 2026
    6: 26,   # Juillet 2026
    7: 31,   # Août 2026
    8: 35,   # Septembre 2026
    9: 39,   # Octobre 2026
    10: 44,  # Novembre 2026
    11: 48   # Décembre 2026
}

# Labels des semaines
WEEK_LABELS = [
    "5 - 11 janv", "12 - 18 janv", "19 - 25 janv", "26 janv - 1 févr",
    "2 - 8 févr", "9 - 15 févr", "16 - 22 févr", "23 févr - 1 mars",
    "2 - 8 mars", "9 - 15 mars", "16 - 22 mars", "23 - 29 mars", "30 mars - 5 avr",
    "6 - 12 avr", "13 - 19 avr", "20 - 26 avr", "27 avr - 3 mai",
    "4 - 10 mai", "11 - 17 mai", "18 - 24 mai", "25 - 31 mai",
    "1 - 7 juin", "8 - 14 juin", "15 - 21 juin", "22 - 28 juin", "29 juin - 5 juil",
    "6 - 12 juil", "13 - 19 juil", "20 - 26 juil", "27 juil - 2 août",
    "3 - 9 août", "10 - 16 août", "17 - 23 août", "24 - 30 août", "31 août - 6 sept",
    "7 - 13 sept", "14 - 20 sept", "21 - 27 sept", "28 sept - 4 oct",
    "5 - 11 oct", "12 - 18 oct", "19 - 25 oct", "26 oct - 1 nov",
    "2 - 8 nov", "9 - 15 nov", "16 - 22 nov", "23 - 29 nov", "30 nov - 6 déc",
    "7 - 13 déc", "14 - 20 déc", "21 - 27 déc", "28 déc - 3 janv"
]

def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_coaches():
    coaches = []
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE role = 'coach'")
    for row in cursor.fetchall():
        coaches.append(row[0])
    conn.close()
    return coaches

def global_index_to_month_week(global_index):
    """Convertit un index global (0-51) en (mois, semaine dans le mois)"""
    for month_idx in range(12):
        offset = WEEK_OFFSETS[month_idx]
        next_offset = WEEK_OFFSETS.get(month_idx + 1, 52)
        weeks_in_month = next_offset - offset

        if global_index < offset + weeks_in_month:
            week_in_month = global_index - offset + 1
            return month_idx, week_in_month

    return 11, 4  # Fallback décembre semaine 4

def calculate_weekly_targets(objectif, cm, ratio_mktg, taux_vente):
    """
    Calcule les objectifs hebdomadaires - IDENTIQUE à generatePlanWeeks de l'entrepreneur
    """
    # Total du pattern (index 1+, > 0)
    total_pattern = sum(pct for i, pct in enumerate(PERCENTAGE_PATTERN) if i >= 1 and pct > 0)

    # Objectif visé avec +10%
    objectif_vise = objectif * 1.10

    mktg_pattern = []
    estim_pattern = []
    contrat_pattern = []
    dollar_pattern = []

    for i in range(52):
        intensity = PERCENTAGE_PATTERN[i]

        if i < 1 or intensity <= 0:
            mktg_pattern.append(0)
            estim_pattern.append(0)
            contrat_pattern.append(0)
            dollar_pattern.append(0)
        else:
            # $ signé
            dollar_semaine = (objectif_vise / total_pattern) * intensity
            dollar_pattern.append(round(dollar_semaine))

            # Contrats
            nb_contrats = dollar_semaine / cm if cm > 0 else 0
            contrat_pattern.append(round(nb_contrats, 1))

            # Estimations (taux_vente est en décimal 0.30 ou pourcentage 30)
            taux = taux_vente if taux_vente < 1 else taux_vente / 100
            nb_estim = nb_contrats / taux if taux > 0 else 0
            estim_pattern.append(round(nb_estim))

            # Heures marketing (ratio_mktg est en décimal 0.85 ou pourcentage 85)
            ratio = ratio_mktg if ratio_mktg < 1 else ratio_mktg / 100
            heures_mktg = nb_estim / ratio if ratio > 0 else 0
            mktg_pattern.append(round(heures_mktg, 1))

    return mktg_pattern, estim_pattern, contrat_pattern, dollar_pattern

def migrate_coach_vise():
    """Migration - calcule les *_vise du coach comme l'entrepreneur"""
    print("=== Migration des *_vise vers les coaches ===")
    print("(Calcul identique à l'entrepreneur)\n")

    coaches = get_coaches()
    print(f"Coaches trouvés: {coaches}\n")

    for coach_username in coaches:
        print(f"\n--- Coach: {coach_username} ---")

        # Charger le RPO du coach
        coach_rpo_file = RPO_DIR / f"{coach_username}_rpo.json"
        coach_rpo = load_json(coach_rpo_file)

        if not coach_rpo:
            print(f"    [SKIP] Pas de fichier RPO")
            continue

        # Récupérer les prévisions du coach (son plan d'affaires)
        coach_previsions = coach_rpo.get('coach_previsions', {})
        objectif = coach_previsions.get('totalObjectif', 0)
        cm = coach_previsions.get('cm', 2500)
        ratio_mktg = coach_previsions.get('ratioMktg', 0.85)
        taux_vente = coach_previsions.get('tauxVente', 0.30)

        print(f"    Objectif: {objectif:,.0f} $")
        print(f"    CM: {cm}, ratioMktg: {ratio_mktg}, tauxVente: {taux_vente}")

        if objectif <= 0:
            print(f"    [SKIP] Pas d'objectif défini")
            continue

        # Calculer les patterns (IDENTIQUE à l'entrepreneur)
        mktg_pattern, estim_pattern, contrat_pattern, dollar_pattern = calculate_weekly_targets(
            objectif, cm, ratio_mktg, taux_vente
        )

        # Initialiser weekly si nécessaire
        if 'weekly' not in coach_rpo:
            coach_rpo['weekly'] = {}

        # Sauvegarder dans le JSON (IDENTIQUE à saveWeeklyTargetsToJSON)
        for global_idx in range(52):
            month_idx, week_in_month = global_index_to_month_week(global_idx)
            month_key = str(month_idx)
            week_key = str(week_in_month)

            # Créer le mois si nécessaire
            if month_key not in coach_rpo['weekly']:
                coach_rpo['weekly'][month_key] = {}

            # Créer la semaine si nécessaire
            if week_key not in coach_rpo['weekly'][month_key]:
                coach_rpo['weekly'][month_key][week_key] = {}

            week_data = coach_rpo['weekly'][month_key][week_key]

            # Ajouter week_label
            if global_idx < len(WEEK_LABELS):
                week_data['week_label'] = WEEK_LABELS[global_idx]

            # Sauvegarder les *_vise (IDENTIQUE à l'entrepreneur)
            week_data['h_marketing_vise'] = mktg_pattern[global_idx]
            week_data['estimation_vise'] = estim_pattern[global_idx]
            week_data['contract_vise'] = contrat_pattern[global_idx]
            week_data['dollar_vise'] = dollar_pattern[global_idx]

            # Ajouter focus vide si pas déjà présent
            if 'focus' not in week_data or week_data['focus'] == '':
                week_data['focus'] = '-'

        # Sauvegarder
        save_json(coach_rpo_file, coach_rpo)
        print(f"    [OK] *_vise + focus sauvegardés")

        # Afficher exemples
        for month, week, label in [('0', '4', '26 janv'), ('1', '1', '2-8 fév')]:
            if month in coach_rpo.get('weekly', {}) and week in coach_rpo['weekly'][month]:
                w = coach_rpo['weekly'][month][week]
                print(f"    Sem {label}: h_vise={w.get('h_marketing_vise', 0)}, "
                      f"est_vise={w.get('estimation_vise', 0)}, "
                      f"dollar_vise={w.get('dollar_vise', 0)}")

    print("\n=== Migration terminée ===")

if __name__ == "__main__":
    migrate_coach_vise()
