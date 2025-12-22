#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour remplacer tous les emojis par des équivalents ASCII
"""

import os
import re

# Mapping des emojis vers leurs équivalents ASCII
EMOJI_REPLACEMENTS = {
    '[OK]': '[OK]',
    '[ERROR]': '[ERROR]',
    '[WARN]': '[WARN]',
    '[ERROR]': '[ERROR]',
    '[FILE]': '[FILE]',
    '[PACKAGE]': '[PACKAGE]',
    '[ADD]': '[ADD]',
    '[DEBUG]': '[DEBUG]',
    '[FIX]': '[FIX]',
    '[INFO]': '[INFO]',
    '[DATA]': '[DATA]',
    '[MONEY]': '[MONEY]',
    '[BAN]': '[BAN]',
    '->': '->',
    '[PROD]': '[PROD]',
    '[STATS]': '[STATS]',
    '[INFO]': '[INFO]',
    '[TARGET]': '[TARGET]',
    '[TIME]': '[TIME]',
    '[DATE]': '[DATE]',
    '[NEW]': '[NEW]',
    '[LAUNCH]': '[LAUNCH]',
    '[POWER]': '[POWER]',
    '[SUCCESS]': '[SUCCESS]',
    '[OK]': '[OK]',
    '[STAR]': '[STAR]',
    '[STAR]': '[STAR]',
    '[CODE]': '[CODE]',
    '[BUG]': '[BUG]',
    '[LOCK]': '[LOCK]',
    '[UNLOCK]': '[UNLOCK]',
    '[NOTE]': '[NOTE]',
    '[DELETE]': '[DELETE]',
    '[FAST]': '[FAST]',
    '[HOT]': '[HOT]',
    '[LOVE]': '[LOVE]',
    '[LIKE]': '[LIKE]',
    '[GREEN]': '[GREEN]',
    '[BLUE]': '[BLUE]',
    '[YELLOW]': '[YELLOW]',
    '[ORANGE]': '[ORANGE]',
    '[PURPLE]': '[PURPLE]',
    '[WHITE]': '[WHITE]',
    '[BLACK]': '[BLACK]',
    '[CHECK]': '[CHECK]',
    '[X]': '[X]',
    '->': '->',
    '<-': '<-',
    '^': '^',
    'v': 'v',
}

def replace_emojis_in_file(filepath):
    """Remplace tous les emojis dans un fichier"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        replacements_made = 0

        # Remplacer chaque emoji
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            if emoji in content:
                count = content.count(emoji)
                content = content.replace(emoji, replacement)
                replacements_made += count

        # Si des modifications ont été faites, sauvegarder
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return replacements_made

        return 0
    except Exception as e:
        with open('emoji_errors.log', 'a', encoding='utf-8') as log:
            log.write(f"Error in {filepath}: {str(e)}\n")
        return 0

def main():
    total_replacements = 0
    files_modified = 0

    # Parcourir tous les fichiers Python
    for root, dirs, files in os.walk('.'):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if d not in ['node_modules', 'dist', '.git', '__pycache__', 'venv', 'env']]

        for file in files:
            # Ne traiter que les fichiers Python et certains HTML
            if file.endswith(('.py', '.html', '.js')):
                filepath = os.path.join(root, file)
                replacements = replace_emojis_in_file(filepath)
                if replacements > 0:
                    total_replacements += replacements
                    files_modified += 1
                    with open('emoji_fix_report.txt', 'a', encoding='utf-8') as report:
                        report.write(f"{filepath}: {replacements} replacements\n")

    # Créer un rapport
    with open('emoji_fix_report.txt', 'a', encoding='utf-8') as report:
        report.write(f"\n===== SUMMARY =====\n")
        report.write(f"Total files modified: {files_modified}\n")
        report.write(f"Total replacements: {total_replacements}\n")

    print(f"Done! {files_modified} files modified, {total_replacements} emojis replaced")
    print("Check emoji_fix_report.txt for details")

if __name__ == '__main__':
    # Supprimer les anciens rapports
    for f in ['emoji_fix_report.txt', 'emoji_errors.log']:
        if os.path.exists(f):
            os.remove(f)

    main()
