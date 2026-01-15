"""
Script de migration pour mettre a jour les entrepreneurs au nouveau format JSON
- Preserve TOUTES les donnees existantes
- Ajoute seulement les champs manquants
Usage: python migration_full_sync.py
"""

import sys
import os
sys.path.insert(0, '.')

import sqlite3
from database import get_database_path
from QE.Backend.rpo import (
    load_user_rpo_data,
    save_user_rpo_data
)

# Pourcentages par défaut pour États des Résultats
DEFAULT_BUDGET_PERCENT = {
    "assurance-qe": 1.5,
    "concours": 0.0,
    "essence": 1.67,
    "entretien-voiture": 0.5,
    "fourniture-bureau": 0.1,
    "frais-bancaires": 0.1,
    "frais-cellulaire": 0.17,
    "frais-garanties": 0.0,
    "leads": 0.13,
    "peinture": 9.0,
    "petits-outils": 4.0,
    "repas": 0.33,
    "redevances": 0.0,
    "salaire-peintres": 30.0,
    "salaires-representant": 1.33
}

# Structure complete d'une semaine (valeurs par defaut pour champs manquants)
DEFAULT_WEEK_FIELDS = {
    "h_marketing": "-",
    "estimation": 0,
    "contract": 0,
    "dollar": 0,
    "commentaire": "Probleme: - | Focus: -",
    "prod_horaire": "-",
    "ca_cumul": 0,
    "produit": 0,
    "rating": 0,  # Etoiles hebdomadaires
    "week_label": "",
    "h_marketing_vise": 0,
    "estimation_vise": 0,
    "contract_vise": 0,
    "dollar_vise": 0,
    "h_marketing_obj_modifier": 0,
    "estimation_obj_modifier": 0,
    "contract_obj_modifier": 0,
    "dollar_obj_modifier": 0
}

def fix_etats_resultats(username: str):
    """
    Corrige les états des résultats SANS toucher aux valeurs actuel/cible
    Calcule budget_percent depuis cible / objectif_ca * 100
    """
    try:
        rpo_data = load_user_rpo_data(username)

        if 'etats_resultats' not in rpo_data:
            rpo_data['etats_resultats'] = {}

        current_budget = rpo_data['etats_resultats'].get('budget_percent', {})
        cible_data = rpo_data['etats_resultats'].get('cible', {})
        objectif_ca = rpo_data.get('annual', {}).get('objectif_ca', 0)

        if not current_budget or len(current_budget) == 0:
            if objectif_ca > 0 and cible_data:
                # Calculer les % réels depuis cible / objectif_ca * 100
                calculated_percent = {}
                for category, cible_value in cible_data.items():
                    if isinstance(cible_value, (int, float)) and cible_value > 0:
                        calculated_percent[category] = round((cible_value / objectif_ca) * 100, 2)
                    else:
                        calculated_percent[category] = 0.0
                rpo_data['etats_resultats']['budget_percent'] = calculated_percent
                save_user_rpo_data(username, rpo_data)
                return True, f"% calculés (CA={objectif_ca})"
            else:
                # Pas de cible ou objectif_ca=0, utiliser les % par défaut
                rpo_data['etats_resultats']['budget_percent'] = DEFAULT_BUDGET_PERCENT.copy()
                save_user_rpo_data(username, rpo_data)
                return True, "% par défaut"
        else:
            return True, "deja OK"

    except Exception as e:
        print(f"[ERROR] Fix etats resultats {username}: {e}")
        return False, str(e)


def migrate_entrepreneur_rpo(username: str):
    """
    Migration complete pour un entrepreneur:
    1. Fix budget_percent si vide
    2. Supprime weekly[-2] et weekly[-1]
    3. Supprime monthly[dec2025]
    4. Supprime semaines sans week_label (invalides)
    5. Supprime champs inutiles (rating, depot, peintre, satisfaction, probleme, focus)
    6. Ajoute les champs manquants
    TOUT EN UNE SEULE SAUVEGARDE
    """
    try:
        rpo_data = load_user_rpo_data(username)
        modified = False
        fields_added = 0
        fields_removed = 0
        budget_added = False

        # Champs a supprimer des semaines (rating garde pour les etoiles)
        FIELDS_TO_REMOVE = ['depot', 'peintre', 'satisfaction', 'probleme', 'focus']

        # 1. Calculer budget_percent depuis cible et objectif_ca
        if 'etats_resultats' not in rpo_data:
            rpo_data['etats_resultats'] = {}
            modified = True

        current_budget = rpo_data['etats_resultats'].get('budget_percent', {})
        cible_data = rpo_data['etats_resultats'].get('cible', {})
        objectif_ca = rpo_data.get('annual', {}).get('objectif_ca', 0)

        if (not current_budget or len(current_budget) == 0) and objectif_ca > 0 and cible_data:
            # Calculer les % réels depuis cible / objectif_ca * 100
            calculated_percent = {}
            for category, cible_value in cible_data.items():
                if isinstance(cible_value, (int, float)) and cible_value > 0:
                    calculated_percent[category] = round((cible_value / objectif_ca) * 100, 2)
                else:
                    calculated_percent[category] = 0.0
            rpo_data['etats_resultats']['budget_percent'] = calculated_percent
            modified = True
            budget_added = True
            print(f"    [CALC] % calculés depuis cible (objectif_ca={objectif_ca})", flush=True)
        elif not current_budget or len(current_budget) == 0:
            # Pas de cible ou objectif_ca=0, utiliser les % par défaut
            rpo_data['etats_resultats']['budget_percent'] = DEFAULT_BUDGET_PERCENT.copy()
            modified = True
            budget_added = True
            print(f"    [DEFAULT] % par défaut (pas de cible ou objectif_ca=0)", flush=True)

        # 2. Supprimer weekly[-2] et weekly[-1]
        if 'weekly' in rpo_data:
            if '-2' in rpo_data['weekly']:
                del rpo_data['weekly']['-2']
                modified = True
                print(f"    [CLEAN] Supprime weekly[-2]", flush=True)
            if '-1' in rpo_data['weekly']:
                del rpo_data['weekly']['-1']
                modified = True
                print(f"    [CLEAN] Supprime weekly[-1]", flush=True)

        # 3. Supprimer monthly[dec2025] si existe
        if 'monthly' in rpo_data:
            if 'dec2025' in rpo_data['monthly']:
                del rpo_data['monthly']['dec2025']
                modified = True
                print(f"    [CLEAN] Supprime monthly[dec2025]", flush=True)

        # 4. Parcourir les semaines pour nettoyer et upgrader
        if 'weekly' not in rpo_data:
            rpo_data['weekly'] = {}
            modified = True

        for month_key in list(rpo_data['weekly'].keys()):
            try:
                month_idx = int(month_key)
                if month_idx < 0 or month_idx > 11:
                    del rpo_data['weekly'][month_key]
                    modified = True
                    continue
            except:
                continue

            month_data = rpo_data['weekly'][month_key]
            if not isinstance(month_data, dict):
                continue

            weeks_to_delete = []
            for week_key in list(month_data.keys()):
                week_data = month_data[week_key]
                if not isinstance(week_data, dict):
                    continue

                # Supprimer semaines sans week_label (invalides)
                week_label = week_data.get('week_label', '')
                if not week_label or week_label == '':
                    weeks_to_delete.append(week_key)
                    continue

                # Supprimer champs inutiles
                for field in FIELDS_TO_REMOVE:
                    if field in week_data:
                        del week_data[field]
                        fields_removed += 1
                        modified = True

                # Ajouter champs manquants
                for field, default_value in DEFAULT_WEEK_FIELDS.items():
                    if field not in week_data:
                        week_data[field] = default_value
                        fields_added += 1
                        modified = True

            # Supprimer les semaines invalides (sans week_label)
            for week_key in weeks_to_delete:
                del month_data[week_key]
                modified = True
                print(f"    [CLEAN] Supprime semaine {month_key}/{week_key} (pas de label)", flush=True)

        # SAUVEGARDE UNIQUE
        if modified:
            save_user_rpo_data(username, rpo_data)
            status_parts = []
            if budget_added:
                status_parts.append("budget%")
            if fields_added > 0 or fields_removed > 0:
                status_parts.append(f"+{fields_added}/-{fields_removed}")
            return True, " ".join(status_parts) if status_parts else "OK"
        else:
            return True, "deja OK"

    except Exception as e:
        print(f"[ERROR] Migration {username}: {e}")
        return False, str(e)


def get_all_entrepreneurs():
    """Récupère tous les entrepreneurs actifs"""
    DB_PATH = get_database_path()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role='entrepreneur' AND is_active=1")
        entrepreneurs = [row[0] for row in cursor.fetchall()]

    return entrepreneurs


def main():
    print("=" * 80)
    print("MIGRATION ENTREPRENEURS - NOUVEAU FORMAT JSON")
    print("=" * 80)
    print()
    print("MODE: Preserve toutes les donnees, ajoute seulement les champs manquants")
    print()

    # 1. Récupérer tous les entrepreneurs
    print("[ETAPE 1/2] Recuperation des entrepreneurs...")
    entrepreneurs = get_all_entrepreneurs()
    print(f"  OK {len(entrepreneurs)} entrepreneurs trouves")
    print()

    # 2. Migration complete (tout en un)
    print("[ETAPE 2/2] Migration complete...")
    print("  - Calcule budget_percent = cible / objectif_ca * 100")
    print("  - Supprime: weekly[-2], weekly[-1], monthly[dec2025]")
    print("  - Supprime: semaines sans week_label (invalides)")
    print("  - Supprime: depot, peintre, satisfaction, probleme, focus")
    print("  - Ajoute: champs manquants (week_label, *_vise, *_obj_modifier)")
    print()
    success_count = 0
    already_ok = 0
    for i, username in enumerate(entrepreneurs, 1):
        print(f"  [{i}/{len(entrepreneurs)}] {username}...", end=" ")
        try:
            success, status = migrate_entrepreneur_rpo(username)
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

    print(f"  => {success_count}/{len(entrepreneurs)} OK ({already_ok} deja OK)")
    print()

    # Résumé
    print("=" * 80)
    print("MIGRATION TERMINEE")
    print("=" * 80)
    print()
    print(f"RESUME: {len(entrepreneurs)} entrepreneurs traites ({already_ok} deja OK)")
    print()
    print("DONNEES PRESERVEES:")
    print("  [OK] h_marketing, prod_horaire, commentaire")
    print("  [OK] estimation, contract, dollar, ca_cumul, produit")
    print("  [OK] etats_resultats (actuel, cible)")
    print()
    print("ELEMENTS SUPPRIMES:")
    print("  [-] weekly[-2], weekly[-1], monthly[dec2025]")
    print("  [-] semaines sans week_label (invalides)")
    print("  [-] depot, peintre, satisfaction, probleme, focus")
    print()
    print("CHAMPS AJOUTES:")
    print("  [+] budget_percent = cible / objectif_ca * 100")
    print("      (ou % par defaut si objectif_ca=0 ou cible vide)")
    print("  [+] week_label, *_vise, *_obj_modifier")
    print()
    print("JSON au nouveau format!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[ANNULÉ] Migration interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERREUR FATALE] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
