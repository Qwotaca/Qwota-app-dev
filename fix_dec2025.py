import re

files = [
    r'QE\Frontend\Entrepreneurs\General\RPO\rpo.html',
    r'QE\Frontend\Coach\coach_rpo.html',
    r'QE\Frontend\Admin\direction_rpo.html'
]

for file_path in files:
    print(f"\nProcessing {file_path}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified_lines = []
        skip_next = 0
        changes = 0

        for i, line in enumerate(lines):
            if skip_next > 0:
                skip_next -= 1
                changes += 1
                continue

            # Supprimer les options avec data-value="-2"
            if 'data-value="-2"' in line:
                # Skip cette ligne et les 2 suivantes (pour multilignes)
                skip_next = 2
                changes += 1
                continue

            # Supprimer les lignes avec '-2': dans les mappings
            if re.search(r"['\"]?-2['\"]?\s*:", line):
                changes += 1
                continue

            # Mettre à jour les dates
            line = line.replace('createTorontoDate(2025, 11, 1)', 'createTorontoDate(2026, 0, 1)')
            line = line.replace('new Date(2025, 11, 1)', 'new Date(2026, 0, 1)')

            # Mettre à jour les commentaires et textes
            if '1er décembre 2025' in line or 'décembre 2025' in line or 'Décembre 2025' in line:
                original = line
                line = line.replace('1er décembre 2025', '1er janvier 2026')
                line = line.replace('décembre 2025', 'janvier 2026')
                line = line.replace('Décembre 2025', 'Janvier 2026')
                if line != original:
                    changes += 1

            # Mettre à jour les références monthIndex
            if 'monthIndex === -2' in line or 'monthIndex >= -2' in line:
                original = line
                line = re.sub(r'monthIndex === -2\s*\|\|\s*', '', line)
                line = re.sub(r'\s*\|\|\s*monthIndex === -2', '', line)
                line = line.replace('monthIndex >= -2', 'monthIndex >= 0')
                if line != original:
                    changes += 1

            # Mettre à jour les boucles
            if 'for (let m = -2; m <= 11; m++)' in line:
                line = line.replace('for (let m = -2; m <= 11; m++)', 'for (let m = 0; m <= 11; m++)')
                changes += 1

            modified_lines.append(line)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)

        print(f"  {len(lines)} lignes -> {len(modified_lines)} lignes ({changes} changements)")

    except Exception as e:
        print(f"  ERREUR: {e}")

print("\nTermine!")
