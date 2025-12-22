import re
import os
import sys
import io

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Fichiers manquants
files_to_update = [
    r'QE\Frontend\Entrepreneurs\Gestions\Facturation QE\Facturation QE.html',
    r'QE\Frontend\Entrepreneurs\Gestions\Avis\avis.html',
]

for file_path in files_to_update:
    if not os.path.exists(file_path):
        print(f"SKIP: {file_path} n'existe pas")
        continue

    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print('='*60)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. Supprimer tout le CSS inline du sélecteur entrepreneur
    css_patterns = [
        r'/\*\s*={40,}\s*ENTREPRENEUR SELECTOR.*?={40,}\s*\*/.*?(?=</style>|<style>|<script>)',
        r'#coach-entrepreneur-selector\s*\{[^}]*\}.*?\.entrepreneur-badge\s*\{[^}]*\}',
        r'/\* Sélecteur Entrepreneur pour Coach/Direction \*/.*?\.entrepreneur-badge\s*\{[^}]*\}',
        r'\.coach-dropdown-container\s*\{.*?\.coach-dropdown-option:active\s*\{[^}]*\}',
        r'\.coach-dropdown\s*\{.*?\.entrepreneur-badge\s*\{[^}]*\}',
        r'body\.coach-mode:not\(\.has-selection\).*?pointer-events:\s*all\s*!important;\s*\}',
    ]

    for pattern in css_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    # 2. Supprimer tout le JavaScript inline du sélecteur
    js_patterns = [
        r'/\*\s*={40,}\s*ENTREPRENEUR SELECTOR.*?={40,}\s*\*/.*?(?=</script>|<script>)',
        r'//\s*={40,}\s*ENTREPRENEUR SELECTOR.*?(?=</script>|<script>)',
        r'//\s*ANTI-FLASH.*?loadEntrepreneursForCoach\(\);.*?\}\);',
        r'//\s*Gestion du dropdown entrepreneur.*?loadEntrepreneursForCoach\(\);.*?\}\);',
        r'async function loadEntrepreneursForCoach\(\).*?\}\s*\}\s*loadEntrepreneursForCoach\(\);',
    ]

    for pattern in js_patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    # 3. Ajouter les liens vers les fichiers partagés dans le <head>
    if 'entrepreneur-selector.css' not in content:
        head_pattern = r'(</head>)'
        replacement = r'  <link rel="stylesheet" href="/entrepreneur-selector.css">\n\1'
        content = re.sub(head_pattern, replacement, content)
        print("✓ Ajout du lien CSS")

    if 'entrepreneur-selector.js' not in content:
        body_pattern = r'(</body>)'
        replacement = r'  <script src="/entrepreneur-selector.js"></script>\n\1'
        content = re.sub(body_pattern, replacement, content)
        print("✓ Ajout du lien JavaScript")

    # 4. Nettoyer les lignes vides multiples
    content = re.sub(r'\n{3,}', '\n\n', content)

    # 5. Sauvegarder seulement si des changements ont été faits
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Fichier mis à jour: {file_path}")
    else:
        print(f"○ Aucun changement nécessaire: {file_path}")

print("\n" + "="*60)
print("Migration des fichiers manquants terminée!")
print("="*60)
