#!/usr/bin/env python3
"""
Script de migration pour calculer les données annuelles RPO.
Agrège les données des entrepreneurs RPO pour populer la section "annual"
des fichiers RPO direction et coach.

Usage:
    python scripts/migrate_annual_rpo.py

Auteur: Migration automatique
Date: 2026-01-20
"""

import json
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Chemins des fichiers
BASE_DIR = Path(__file__).parent.parent

# Détection de l'environnement (Render vs local)
if sys.platform == 'win32':
    # Windows (local)
    DATA_DIR = BASE_DIR / "cloud"
    DB_PATH = BASE_DIR / "data" / "qwota.db"
else:
    # Linux (Render)
    DATA_DIR = Path("/mnt/cloud")
    DB_PATH = Path("/mnt/cloud/qwota.db")

RPO_DIR = DATA_DIR / "rpo"


def load_json(filepath):
    """Charge un fichier JSON."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR] Impossible de charger {filepath}: {e}")
        return None


def save_json(filepath, data):
    """Sauvegarde un fichier JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Fichier sauvegardé: {filepath}")
        return True
    except Exception as e:
        print(f"[ERREUR] Impossible de sauvegarder {filepath}: {e}")
        return False


def get_entrepreneur_grade(username):
    """Récupère le grade d'un entrepreneur depuis son user_info.json."""
    user_info_path = DATA_DIR / "signatures" / username / "user_info.json"
    data = load_json(user_info_path)
    if data:
        grade = data.get('grade', 'recrue')
        # Normaliser le grade (senior, senior2, etc. -> senior)
        if grade and grade.startswith('senior'):
            return 'senior'
        return 'recrue'
    return 'recrue'


def get_entrepreneurs_from_db():
    """Récupère la liste des entrepreneurs depuis la base de données."""
    entrepreneurs = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, assigned_coach FROM users WHERE role = 'entrepreneur' AND is_active = 1")
        rows = cursor.fetchall()
        for row in rows:
            username = row[0]
            grade = get_entrepreneur_grade(username)
            entrepreneurs.append({
                'username': username,
                'coach': row[1],
                'grade': grade
            })
            print(f"  - {username}: coach={row[1]}, grade={grade}")
        conn.close()
        print(f"[INFO] {len(entrepreneurs)} entrepreneurs trouvés dans la DB")
    except Exception as e:
        print(f"[ERREUR] Impossible de lire la DB: {e}")
    return entrepreneurs


def get_entrepreneur_rpo_annual(username):
    """
    Récupère les données annual d'un entrepreneur depuis son fichier RPO.
    """
    filepath = RPO_DIR / f"{username}_rpo.json"
    data = load_json(filepath)

    if not data:
        return None

    annual = data.get('annual', {})
    weekly = data.get('weekly', {})

    # Calculer h_pap sans semaine 1 depuis weekly
    h_pap_sans_week1 = 0
    h_pap_total = 0
    for month_id, weeks in weekly.items():
        for week_id, week_data in weeks.items():
            if not week_data.get('week_label'):
                continue
            h_val = week_data.get('h_marketing', 0)
            h_marketing = float(h_val) if h_val and h_val != '-' else 0
            h_pap_total += h_marketing
            # Exclure semaine 1 du mois 0 (5-11 janv)
            if not (str(month_id) == "0" and str(week_id) == "1"):
                h_pap_sans_week1 += h_marketing

    return {
        'username': username,
        'objectif_ca': annual.get('objectif_ca', 0),
        'hr_pap_reel': annual.get('hr_pap_reel', 0),
        'hr_pap_reel_sans_week1': h_pap_sans_week1,
        'estimation_reel': annual.get('estimation_reel', 0),
        'contract_reel': annual.get('contract_reel', 0),
        'dollar_reel': annual.get('dollar_reel', 0),
        'mktg_reel': annual.get('mktg_reel', 0),
        'vente_reel': annual.get('vente_reel', 0),
        'moyen_reel': annual.get('moyen_reel', 0),
        'prod_horaire': annual.get('prod_horaire', 0),
        'ratio_mktg': annual.get('ratio_mktg', 85),
        'cm_prevision': annual.get('cm_prevision', 2500),
        'taux_vente': annual.get('taux_vente', 30)
    }


def calculate_weekly_totals_sans_week1(weekly_data):
    """
    Calcule le total h_marketing excluant la semaine 1 du mois 0.
    """
    h_pap_sans_week1 = 0
    h_pap_total = 0

    for month_id, weeks in weekly_data.items():
        for week_id, week_data in weeks.items():
            if not week_data.get('week_label'):
                continue
            h_val = week_data.get('h_marketing', 0)
            h_marketing = float(h_val) if h_val and h_val != '-' else 0
            h_pap_total += h_marketing
            # Exclure semaine 1 du mois 0 (5-11 janv)
            if not (str(month_id) == "0" and str(week_id) == "1"):
                h_pap_sans_week1 += h_marketing

    return h_pap_total, h_pap_sans_week1


def migrate_coach_annual(coach_username, entrepreneurs_data):
    """
    Migre les données annuelles pour un coach.
    Agrège les données des entrepreneurs du coach.
    """
    print(f"\n[INFO] Migration coach: {coach_username}")

    coach_rpo_path = RPO_DIR / f"{coach_username}_rpo.json"
    coach_data = load_json(coach_rpo_path)

    if not coach_data:
        print(f"[WARN] Fichier {coach_rpo_path} non trouvé")
        return False

    # Filtrer les entrepreneurs de ce coach
    coach_entrepreneurs = [e for e in entrepreneurs_data if e and e.get('coach') == coach_username]
    print(f"  - Entrepreneurs du coach: {len(coach_entrepreneurs)}")

    # Agréger les données annual des entrepreneurs
    total_objectif = 0
    total_hr_pap = 0
    total_hr_pap_sans_week1 = 0
    total_estimation = 0
    total_contract = 0
    total_dollar = 0
    nb_entrepreneurs = 0

    # Comptage par grade
    estimation_recrue = 0
    estimation_senior = 0
    nb_recrue = 0
    nb_senior = 0

    total_prod_horaire = 0
    nb_prod_horaire = 0

    for ent in coach_entrepreneurs:
        username = ent.get('username')
        grade = ent.get('grade', 'recrue')
        if not username:
            continue

        rpo_annual = get_entrepreneur_rpo_annual(username)
        if rpo_annual:
            total_objectif += rpo_annual['objectif_ca']
            total_hr_pap += rpo_annual['hr_pap_reel']
            total_hr_pap_sans_week1 += rpo_annual['hr_pap_reel_sans_week1']
            total_estimation += rpo_annual['estimation_reel']
            total_contract += rpo_annual['contract_reel']
            total_dollar += rpo_annual['dollar_reel']
            nb_entrepreneurs += 1

            # Agréger prod_horaire (moyenne des entrepreneurs qui ont des valeurs)
            ent_prod_h = rpo_annual.get('prod_horaire', 0)
            if ent_prod_h and ent_prod_h > 0:
                total_prod_horaire += ent_prod_h
                nb_prod_horaire += 1

            # Agréger par grade
            if grade == 'senior':
                estimation_senior += rpo_annual['estimation_reel']
                nb_senior += 1
            else:
                estimation_recrue += rpo_annual['estimation_reel']
                nb_recrue += 1

            print(f"    + {username} ({grade}): hr_pap={rpo_annual['hr_pap_reel']}, est={rpo_annual['estimation_reel']}, contract={rpo_annual['contract_reel']}, dollar={rpo_annual['dollar_reel']}, prod_h={ent_prod_h}")

    # Calculer h_pap depuis weekly du coach aussi
    weekly = coach_data.get('weekly', {})
    coach_h_pap_total, coach_h_pap_sans_week1 = calculate_weekly_totals_sans_week1(weekly)

    # Utiliser les valeurs du weekly coach si disponibles, sinon sum des entrepreneurs
    hr_pap_reel = coach_h_pap_total if coach_h_pap_total > 0 else total_hr_pap
    hr_pap_sans_week1 = coach_h_pap_sans_week1 if coach_h_pap_sans_week1 > 0 else total_hr_pap_sans_week1

    # Calculer les métriques
    # Taux marketing = estimation_reel / h_pap_sans_week1 (ratio, pas pourcentage)
    # Taux marketing = estimation_reel / hr_pap_total (estimations par heure)
    mktg_reel = (total_estimation / hr_pap_reel) if hr_pap_reel > 0 else 0

    # Taux de vente = contract_reel / estimation_reel * 100
    vente_reel = (total_contract / total_estimation * 100) if total_estimation > 0 else 0

    # Contrat moyen = dollar_reel / contract_reel
    moyen_reel = (total_dollar / total_contract) if total_contract > 0 else 0

    # Productivité horaire = moyenne des prod_horaire des entrepreneurs
    prod_horaire = (total_prod_horaire / nb_prod_horaire) if nb_prod_horaire > 0 else 0

    print(f"  - Totaux: hr_pap={hr_pap_reel}, hr_pap_sans_w1={hr_pap_sans_week1}, est={total_estimation}, contract={total_contract}, dollar={total_dollar}")
    print(f"  - Métriques: mktg={mktg_reel:.2f}, vente={vente_reel:.2f}, moyen={moyen_reel:.2f}, prod_h={prod_horaire:.2f}")
    print(f"  - Par grade: recrue={estimation_recrue} (n={nb_recrue}), senior={estimation_senior} (n={nb_senior})")

    # Récupérer les prévisions du coach
    coach_previsions = coach_data.get('coach_previsions', {})

    # Mettre à jour la section annual
    annual = coach_data.get('annual', {})
    annual.update({
        'hr_pap_reel': hr_pap_reel,
        'hr_pap_reel_sans_week1': hr_pap_sans_week1,
        'estimation_reel': total_estimation,
        'estimation_reel_recrue': estimation_recrue,
        'estimation_reel_senior': estimation_senior,
        'nb_recrue': nb_recrue,
        'nb_senior': nb_senior,
        'contract_reel': total_contract,
        'dollar_reel': total_dollar,
        'mktg_reel': round(mktg_reel, 2),
        'vente_reel': round(vente_reel, 2),
        'moyen_reel': round(moyen_reel, 2),
        'prod_horaire': round(prod_horaire, 2),
        'nb_entrepreneurs': nb_entrepreneurs,
        'ratio_mktg': coach_previsions.get('ratioMktg', 85),
        'cm_prevision': coach_previsions.get('cm', 2500),
        'taux_vente': coach_previsions.get('tauxVente', 30)
    })

    coach_data['annual'] = annual
    coach_data['last_updated'] = datetime.now().isoformat()

    return save_json(coach_rpo_path, coach_data)


def migrate_direction_annual(entrepreneurs_data, coaches):
    """
    Migre les données annuelles pour direction_rpo.json.
    Agrège les données de tous les entrepreneurs.
    """
    print("\n" + "="*60)
    print("MIGRATION DIRECTION RPO - ANNUAL")
    print("="*60)

    direction_rpo_path = RPO_DIR / "direction_rpo.json"
    direction_data = load_json(direction_rpo_path)

    if not direction_data:
        print("[ERREUR] Fichier direction_rpo.json non trouvé ou invalide")
        return False

    # Calculer h_pap depuis weekly direction
    weekly = direction_data.get('weekly', {})
    dir_h_pap_total, dir_h_pap_sans_week1 = calculate_weekly_totals_sans_week1(weekly)

    print(f"[INFO] H PAP direction weekly: total={dir_h_pap_total}, sans_week1={dir_h_pap_sans_week1}")

    # Agréger les données annual de TOUS les entrepreneurs
    total_objectif = 0
    total_hr_pap = 0
    total_hr_pap_sans_week1 = 0
    total_estimation = 0
    total_contract = 0
    total_dollar = 0
    nb_entrepreneurs = 0

    # Comptage par grade
    estimation_recrue = 0
    estimation_senior = 0
    nb_recrue = 0
    nb_senior = 0
    total_prod_horaire = 0
    nb_prod_horaire = 0

    for ent in entrepreneurs_data:
        username = ent.get('username')
        grade = ent.get('grade', 'recrue')
        if not username:
            continue

        rpo_annual = get_entrepreneur_rpo_annual(username)
        if rpo_annual:
            total_objectif += rpo_annual['objectif_ca']
            total_hr_pap += rpo_annual['hr_pap_reel']
            total_hr_pap_sans_week1 += rpo_annual['hr_pap_reel_sans_week1']
            total_estimation += rpo_annual['estimation_reel']
            total_contract += rpo_annual['contract_reel']
            total_dollar += rpo_annual['dollar_reel']
            nb_entrepreneurs += 1

            # Agréger prod_horaire
            ent_prod_h = rpo_annual.get('prod_horaire', 0)
            if ent_prod_h and ent_prod_h > 0:
                total_prod_horaire += ent_prod_h
                nb_prod_horaire += 1

            # Agréger par grade
            if grade == 'senior':
                estimation_senior += rpo_annual['estimation_reel']
                nb_senior += 1
            else:
                estimation_recrue += rpo_annual['estimation_reel']
                nb_recrue += 1

            print(f"  + {username} ({grade}): hr_pap={rpo_annual['hr_pap_reel']}, est={rpo_annual['estimation_reel']}, contract={rpo_annual['contract_reel']}, dollar={rpo_annual['dollar_reel']}, prod_h={ent_prod_h}")

    # Utiliser h_pap du weekly direction si disponible
    hr_pap_reel = dir_h_pap_total if dir_h_pap_total > 0 else total_hr_pap
    hr_pap_sans_week1 = dir_h_pap_sans_week1 if dir_h_pap_sans_week1 > 0 else total_hr_pap_sans_week1

    # Calculer les métriques
    # Taux marketing = estimation_reel / hr_pap_total (estimations par heure)
    mktg_reel = (total_estimation / hr_pap_reel) if hr_pap_reel > 0 else 0
    vente_reel = (total_contract / total_estimation * 100) if total_estimation > 0 else 0
    moyen_reel = (total_dollar / total_contract) if total_contract > 0 else 0
    # Productivité horaire = moyenne des prod_horaire des entrepreneurs
    prod_horaire = (total_prod_horaire / nb_prod_horaire) if nb_prod_horaire > 0 else 0

    print(f"\n[INFO] Agrégation direction:")
    print(f"  - H PAP réel: {hr_pap_reel}")
    print(f"  - H PAP sans week1: {hr_pap_sans_week1}")
    print(f"  - Estimations: {total_estimation}")
    print(f"  - Contrats: {total_contract}")
    print(f"  - Dollars: {total_dollar}")
    print(f"  - Taux marketing: {mktg_reel:.2f} ({total_estimation}/{hr_pap_reel})")
    print(f"  - Taux vente: {vente_reel:.2f}%")
    print(f"  - Contrat moyen: {moyen_reel:.2f}$")
    print(f"  - Par grade: recrue={estimation_recrue} (n={nb_recrue}), senior={estimation_senior} (n={nb_senior})")

    # Récupérer les prévisions direction
    direction_previsions = direction_data.get('direction_previsions', {})

    # Mettre à jour la section annual
    annual = direction_data.get('annual', {})
    annual.update({
        'hr_pap_reel': hr_pap_reel,
        'hr_pap_reel_sans_week1': hr_pap_sans_week1,
        'estimation_reel': total_estimation,
        'estimation_reel_recrue': estimation_recrue,
        'estimation_reel_senior': estimation_senior,
        'nb_recrue': nb_recrue,
        'nb_senior': nb_senior,
        'contract_reel': total_contract,
        'dollar_reel': total_dollar,
        'mktg_reel': round(mktg_reel, 2),
        'vente_reel': round(vente_reel, 2),
        'moyen_reel': round(moyen_reel, 2),
        'prod_horaire': round(prod_horaire, 2),
        'nb_entrepreneurs': nb_entrepreneurs,
        'nb_coaches': len(coaches),
        'ratio_mktg': direction_previsions.get('ratioMktg', 85),
        'cm_prevision': direction_previsions.get('cm', 2500),
        'taux_vente': direction_previsions.get('tauxVente', 30)
    })

    direction_data['annual'] = annual
    direction_data['last_updated'] = datetime.now().isoformat()

    if save_json(direction_rpo_path, direction_data):
        print("\n[SUCCESS] Direction RPO annual migré avec succès!")
        return True

    return False


def get_coaches_from_db():
    """Récupère la liste des coaches depuis la base de données."""
    coaches = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role = 'coach' AND is_active = 1")
        rows = cursor.fetchall()
        for row in rows:
            coaches.append(row[0])
        conn.close()
        print(f"[INFO] {len(coaches)} coaches trouvés dans la DB")
    except Exception as e:
        print(f"[ERREUR] Impossible de lire la DB: {e}")
    return coaches


def main():
    """Point d'entrée principal du script de migration."""
    print("="*60)
    print("SCRIPT DE MIGRATION RPO ANNUAL")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Vérifier que les dossiers existent
    if not RPO_DIR.exists():
        print(f"[ERREUR] Dossier RPO non trouvé: {RPO_DIR}")
        return 1

    if not DB_PATH.exists():
        print(f"[ERREUR] Base de données non trouvée: {DB_PATH}")
        return 1

    # Récupérer les entrepreneurs et coaches depuis la DB
    entrepreneurs = get_entrepreneurs_from_db()
    coaches = get_coaches_from_db()

    # Utiliser directement les entrepreneurs avec leurs données (username, coach, grade)
    entrepreneurs_with_coach = entrepreneurs

    # Migrer chaque coach
    print("\n" + "="*60)
    print("MIGRATION COACHES RPO - ANNUAL")
    print("="*60)

    coach_success = 0
    for coach_username in coaches:
        if migrate_coach_annual(coach_username, entrepreneurs_with_coach):
            coach_success += 1

    # Migrer direction
    direction_success = migrate_direction_annual(entrepreneurs_with_coach, coaches)

    print("\n" + "="*60)
    print("RÉSUMÉ DE LA MIGRATION")
    print("="*60)
    print(f"Coaches migrés: {coach_success}/{len(coaches)}")
    print(f"Direction: {'OK' if direction_success else 'ÉCHEC'}")

    if direction_success and coach_success == len(coaches):
        print("\n[SUCCESS] Migration terminée avec succès!")
        return 0
    else:
        print("\n[WARN] Migration terminée avec des erreurs")
        return 1


if __name__ == "__main__":
    sys.exit(main())
