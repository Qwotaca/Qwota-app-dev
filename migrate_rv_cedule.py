"""
Script de migration pour ajouter rv_cedule à toutes les semaines dans les fichiers RPO
Exécuter une seule fois pour initialiser le champ dans tous les fichiers existants.
"""

import json
import os
from pathlib import Path

def migrate_rpo_files():
    """Ajoute rv_cedule: 0 à toutes les semaines de tous les fichiers RPO"""

    rpo_dir = Path("data/rpo")

    if not rpo_dir.exists():
        print(f"[ERROR] Dossier {rpo_dir} non trouve")
        return

    rpo_files = list(rpo_dir.glob("*_rpo.json"))
    print(f"[INFO] {len(rpo_files)} fichiers RPO trouves")

    migrated_count = 0
    weeks_updated = 0

    for rpo_file in rpo_files:
        try:
            with open(rpo_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            modified = False

            # Parcourir tous les mois
            if 'weekly' in data:
                for month_key, month_data in data['weekly'].items():
                    if isinstance(month_data, dict):
                        # Parcourir toutes les semaines du mois
                        for week_key, week_data in month_data.items():
                            if isinstance(week_data, dict):
                                # Ajouter rv_cedule si absent
                                if 'rv_cedule' not in week_data:
                                    week_data['rv_cedule'] = 0
                                    modified = True
                                    weeks_updated += 1

            if modified:
                # Sauvegarder le fichier modifie
                with open(rpo_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                migrated_count += 1
                print(f"[OK] {rpo_file.name} migre")
            else:
                print(f"[SKIP] {rpo_file.name} deja a jour")

        except Exception as e:
            print(f"[ERROR] Erreur avec {rpo_file.name}: {e}")

    print(f"\n[RESUME]")
    print(f"   - Fichiers migres: {migrated_count}/{len(rpo_files)}")
    print(f"   - Semaines mises a jour: {weeks_updated}")

if __name__ == "__main__":
    migrate_rpo_files()
