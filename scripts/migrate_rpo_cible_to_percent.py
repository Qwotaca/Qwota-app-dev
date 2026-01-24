"""
Script de migration RPO: Convertir les $ cible en % budget_percent

Ce script:
1. Lit tous les fichiers RPO JSON
2. Pour chaque fichier avec etats_resultats.cible:
   - Prend l'objectif_ca de annual
   - Calcule le pourcentage pour chaque dépense: (cible / objectif_ca) * 100
   - Sauvegarde dans budget_percent
   - Supprime cible et cible_percent
3. Sauvegarde les fichiers mis à jour
"""

import json
import os
import sys

# Ajouter le chemin du backend pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'QE', 'Backend'))

# Dossier des données RPO - dépend de l'environnement
if sys.platform == 'win32':
    # Windows (développement local)
    RPO_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'rpo')
else:
    # Linux/Unix (Render production)
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")
    RPO_DATA_DIR = os.path.join(base_cloud, "rpo")


def migrate_rpo_file(filepath: str) -> bool:
    """
    Migre un fichier RPO: convertit cible ($) en budget_percent (%)
    Retourne True si migration effectuée, False sinon
    """
    filename = os.path.basename(filepath)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERREUR] Impossible de lire {filename}: {e}")
        return False

    # Vérifier si etats_resultats existe
    if 'etats_resultats' not in data:
        print(f"[SKIP] {filename}: pas de etats_resultats")
        return False

    etats = data['etats_resultats']

    # Vérifier si cible existe
    if 'cible' not in etats or not etats['cible']:
        print(f"[SKIP] {filename}: pas de cible à migrer")
        return False

    # Récupérer objectif_ca
    objectif_ca = data.get('annual', {}).get('objectif_ca', 0)
    if objectif_ca <= 0:
        print(f"[ERREUR] {filename}: objectif_ca invalide ({objectif_ca})")
        return False

    print(f"\n[MIGRATION] {filename}")
    print(f"  objectif_ca: {objectif_ca:,.0f} $")
    print(f"  Dépenses à convertir: {len(etats['cible'])}")

    # Calculer les pourcentages
    budget_percent = {}
    for key, dollars in etats['cible'].items():
        if dollars is not None and isinstance(dollars, (int, float)):
            percent = (dollars / objectif_ca) * 100
            budget_percent[key] = round(percent, 2)
            print(f"    {key}: {dollars:,.0f} $ -> {percent:.2f} %")

    # Mettre à jour les données
    etats['budget_percent'] = budget_percent

    # Supprimer cible et cible_percent
    if 'cible' in etats:
        del etats['cible']
        print(f"  [OK] Supprimé: cible")
    if 'cible_percent' in etats:
        del etats['cible_percent']
        print(f"  [OK] Supprimé: cible_percent")

    # Sauvegarder
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  [OK] Fichier sauvegardé")
        return True
    except Exception as e:
        print(f"  [ERREUR] Impossible de sauvegarder: {e}")
        return False


def main():
    print("=" * 60)
    print("MIGRATION RPO: Conversion cible ($) -> budget_percent (%)")
    print("=" * 60)

    if not os.path.exists(RPO_DATA_DIR):
        print(f"[ERREUR] Dossier RPO non trouvé: {RPO_DATA_DIR}")
        return

    # Lister tous les fichiers JSON
    json_files = [f for f in os.listdir(RPO_DATA_DIR) if f.endswith('_rpo.json')]
    print(f"\nFichiers RPO trouvés: {len(json_files)}")

    migrated = 0
    skipped = 0
    errors = 0

    for filename in json_files:
        filepath = os.path.join(RPO_DATA_DIR, filename)
        result = migrate_rpo_file(filepath)
        if result:
            migrated += 1
        elif result is False:
            # Vérifier si c'est une erreur ou un skip
            skipped += 1

    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"  Fichiers migrés: {migrated}")
    print(f"  Fichiers ignorés: {skipped}")
    print(f"  Erreurs: {errors}")
    print("\nMigration terminée!")


if __name__ == "__main__":
    main()
