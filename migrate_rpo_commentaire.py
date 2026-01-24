#!/usr/bin/env python3
"""
Script de migration RPO: Convertit le format commentaire vers probleme/focus séparés

Ce script:
1. Parcourt tous les fichiers *_rpo.json
2. Pour chaque semaine, parse le champ "commentaire" (format: "Problème: xxx | Focus: yyy")
3. Extrait les valeurs et les met dans des champs séparés "probleme" et "focus"
4. Supprime le champ "commentaire"
5. Sauvegarde le fichier mis à jour

Usage:
    python migrate_rpo_commentaire.py [--dry-run] [--path /chemin/vers/rpo]

    --dry-run : Affiche les changements sans modifier les fichiers
    --path    : Chemin vers le dossier contenant les fichiers RPO (défaut: data/rpo pour local, /mnt/cloud/rpo pour prod)
"""

import json
import os
import sys
import re
from datetime import datetime

def parse_commentaire(commentaire: str) -> tuple:
    """
    Parse le champ commentaire au format "Problème: xxx | Focus: yyy"
    Retourne (probleme, focus)
    """
    if not commentaire:
        return '-', '-'

    probleme = '-'
    focus = '-'

    # Format: "Problème: xxx | Focus: yyy"
    parts = commentaire.split('|')

    for part in parts:
        part = part.strip()
        if part.startswith('Problème:'):
            probleme = part.replace('Problème:', '').strip()
        elif part.startswith('Focus:'):
            focus = part.replace('Focus:', '').strip()

    # Si vide, mettre "-"
    if not probleme or probleme == '':
        probleme = '-'
    if not focus or focus == '':
        focus = '-'

    return probleme, focus


def migrate_rpo_file(filepath: str, dry_run: bool = False) -> dict:
    """
    Migre un fichier RPO du format commentaire vers probleme/focus séparés
    Retourne un dict avec les stats de migration
    """
    stats = {
        'file': os.path.basename(filepath),
        'weeks_migrated': 0,
        'weeks_already_ok': 0,
        'commentaires_removed': 0,
        'errors': []
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        stats['errors'].append(f"Erreur lecture: {e}")
        return stats

    if 'weekly' not in data:
        stats['errors'].append("Pas de données weekly")
        return stats

    modified = False

    # Parcourir tous les mois et semaines
    for month_key, weeks in data['weekly'].items():
        if not isinstance(weeks, dict):
            continue

        for week_key, week_data in weeks.items():
            if not isinstance(week_data, dict):
                continue

            # Vérifier si probleme/focus existent déjà avec des vraies valeurs
            has_probleme = 'probleme' in week_data and week_data['probleme'] and week_data['probleme'] != '-'
            has_focus = 'focus' in week_data and week_data['focus'] and week_data['focus'] != '-'

            # Si les deux existent avec des vraies valeurs, pas besoin de migrer
            if has_probleme and has_focus:
                stats['weeks_already_ok'] += 1
            else:
                # Parser le commentaire si présent
                if 'commentaire' in week_data:
                    parsed_probleme, parsed_focus = parse_commentaire(week_data['commentaire'])

                    # Utiliser les valeurs parsées seulement si les champs n'existent pas ou sont "-"
                    if not has_probleme and parsed_probleme != '-':
                        week_data['probleme'] = parsed_probleme
                        modified = True
                        stats['weeks_migrated'] += 1
                    elif 'probleme' not in week_data:
                        week_data['probleme'] = '-'
                        modified = True

                    if not has_focus and parsed_focus != '-':
                        week_data['focus'] = parsed_focus
                        modified = True
                    elif 'focus' not in week_data:
                        week_data['focus'] = '-'
                        modified = True
                else:
                    # Pas de commentaire, juste initialiser les champs manquants
                    if 'probleme' not in week_data:
                        week_data['probleme'] = '-'
                        modified = True
                    if 'focus' not in week_data:
                        week_data['focus'] = '-'
                        modified = True

            # Supprimer le champ commentaire s'il existe
            if 'commentaire' in week_data:
                del week_data['commentaire']
                stats['commentaires_removed'] += 1
                modified = True

    # Sauvegarder si modifié
    if modified and not dry_run:
        try:
            # Mettre à jour last_updated
            data['last_updated'] = datetime.now().isoformat()

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            stats['errors'].append(f"Erreur sauvegarde: {e}")

    return stats


def main():
    # Parser les arguments
    dry_run = '--dry-run' in sys.argv

    # Déterminer le chemin
    path = None
    for i, arg in enumerate(sys.argv):
        if arg == '--path' and i + 1 < len(sys.argv):
            path = sys.argv[i + 1]

    if not path:
        # Déterminer automatiquement selon l'OS
        if sys.platform == 'win32':
            # Local Windows
            path = os.path.join(os.path.dirname(__file__), 'data', 'rpo')
        else:
            # Production Linux (Render)
            path = '/mnt/cloud/rpo'

    print(f"=" * 60)
    print(f"Migration RPO: commentaire -> probleme/focus")
    print(f"=" * 60)
    print(f"Chemin: {path}")
    print(f"Mode: {'DRY RUN (aucune modification)' if dry_run else 'LIVE (modifications actives)'}")
    print(f"=" * 60)

    if not os.path.exists(path):
        print(f"ERREUR: Le chemin n'existe pas: {path}")
        sys.exit(1)

    # Trouver tous les fichiers *_rpo.json
    rpo_files = [f for f in os.listdir(path) if f.endswith('_rpo.json')]

    print(f"Fichiers trouvés: {len(rpo_files)}")
    print()

    total_stats = {
        'files_processed': 0,
        'weeks_migrated': 0,
        'weeks_already_ok': 0,
        'commentaires_removed': 0,
        'errors': []
    }

    for filename in sorted(rpo_files):
        filepath = os.path.join(path, filename)
        stats = migrate_rpo_file(filepath, dry_run)

        total_stats['files_processed'] += 1
        total_stats['weeks_migrated'] += stats['weeks_migrated']
        total_stats['weeks_already_ok'] += stats['weeks_already_ok']
        total_stats['commentaires_removed'] += stats['commentaires_removed']
        total_stats['errors'].extend(stats['errors'])

        # Afficher le résultat pour ce fichier
        status = "[OK]" if not stats['errors'] else "[ERR]"
        migrated = f"migré:{stats['weeks_migrated']}" if stats['weeks_migrated'] > 0 else ""
        removed = f"supprimé:{stats['commentaires_removed']}" if stats['commentaires_removed'] > 0 else ""

        details = ", ".join(filter(None, [migrated, removed]))
        if details:
            print(f"{status} {filename}: {details}")
        else:
            print(f"{status} {filename}: deja OK")

        if stats['errors']:
            for err in stats['errors']:
                print(f"  [WARN] {err}")

    # Résumé final
    print()
    print(f"=" * 60)
    print(f"RÉSUMÉ")
    print(f"=" * 60)
    print(f"Fichiers traités:     {total_stats['files_processed']}")
    print(f"Semaines migrées:     {total_stats['weeks_migrated']}")
    print(f"Semaines déjà OK:     {total_stats['weeks_already_ok']}")
    print(f"Commentaires retirés: {total_stats['commentaires_removed']}")
    print(f"Erreurs:              {len(total_stats['errors'])}")

    if dry_run:
        print()
        print(">>> Mode DRY RUN: Aucune modification effectuée")
        print(">>> Relancez sans --dry-run pour appliquer les changements")


if __name__ == '__main__':
    main()
