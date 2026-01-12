import re

files = [
    r'QE\Frontend\Entrepreneurs\General\RPO\rpo.html',
    r'QE\Frontend\Coach\coach_rpo.html',
    r'QE\Frontend\Admin\direction_rpo.html'
]

for file_path in files:
    print(f"\n=== Processing {file_path} ===")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_lines = len(content.split('\n'))

        # 1. Retirer les lignes option dropdown pour "Décembre 2025"
        content = re.sub(r'^\s*<div class="custom-select-option"[^>]*data-value="-2"[^>]*>Décembre 2025</div>\s*$', '', content, flags=re.MULTILINE)

        # 2. Changer le label par défaut de "Décembre 2025" à "Janvier 2026"
        content = content.replace('Objectifs et résultats mensuels - Décembre 2025', 'Objectifs et résultats mensuels - Janvier 2026')
        content = content.replace('Objectifs et résultats hebdomadaires - Décembre 2025', 'Objectifs et résultats hebdomadaires - Janvier 2026')

        # 3. Dans les mappings monthInfo, retirer l'index -2
        content = re.sub(r"^\s*'-2':\s*\{[^}]+\},\s*$", '', content, flags=re.MULTILINE)

        # 4. Changer les dates de début du plan de décembre 2025 à janvier 2026
        # createTorontoDate(2025, 11, 1) -> createTorontoDate(2026, 0, 1)
        content = content.replace('createTorontoDate(2025, 11, 1)', 'createTorontoDate(2026, 0, 1)')
        content = content.replace('new Date(2025, 11, 1)', 'new Date(2026, 0, 1)')

        # 5. Mettre à jour les commentaires
        content = content.replace('1er décembre 2025', '1er janvier 2026')
        content = content.replace('décembre 2025', 'janvier 2026')
        content = content.replace('Décembre 2025', 'Janvier 2026')
        content = content.replace('Dec 2025', 'Jan 2026')
        content = content.replace('dec2025', 'jan2026')

        # 6. Ajuster le nombre de semaines de 52 à 47 (car on retire ~5 semaines de décembre)
        # Non, gardons 52 semaines mais qui commencent en janvier

        # 7. Retirer les références à monthIndex === -2
        content = re.sub(r'\s*\|\|\s*monthIndex === -2', '', content)
        content = re.sub(r'monthIndex === -2\s*\|\|\s*', '', content)

        # 8. Retirer les mappages avec -2:
        content = re.sub(r"^\s*'-2':\s*[^,\n]+,?\s*$", '', content, flags=re.MULTILINE)

        # 9. Mettre à jour les boucles qui incluent -2
        content = content.replace('monthIndex >= -2', 'monthIndex >= 0')
        content = content.replace('for (let m = -2; m <= 11; m++)', 'for (let m = 0; m <= 11; m++)')

        # 10. Retirer commentaires "Décembre 2025 (index -2)"
        content = re.sub(r'//.*Décembre 2025.*\n', '', content)
        content = re.sub(r'//.*décembre 2025.*\n', '', content)

        # 11. Dans le mapping dec2025: -2, le retirer
        content = re.sub(r"'dec2025':\s*-2,?\s*\n", '', content)

        # 12. Retirer les cas spéciaux pour Décembre 2025
        content = re.sub(r'if \(monthIndex === -2\) \{[^}]*\} else if', 'if', content)

        new_lines = len(content.split('\n'))

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Modifié: {original_lines} lignes -> {new_lines} lignes (diff: {original_lines - new_lines})")

    except Exception as e:
        print(f"❌ Erreur: {e}")

print("\n✅ Terminé!")
