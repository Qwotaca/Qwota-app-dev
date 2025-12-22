import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = [
    r'QE\Frontend\Entrepreneurs\Gestions\Employes\gestionemployes.html',
    r'QE\Frontend\Entrepreneurs\Gestions\Ventes\Ventes.html',
    r'QE\Frontend\Entrepreneurs\General\RPO\rpo.html',
]

for file_path in files:
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print('='*60)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Commenter l'appel à loadEntrepreneursForCoach();
    content = re.sub(
        r'(\s+)(loadEntrepreneursForCoach\(\);)',
        r'\1// \2  // Désactivé - géré par entrepreneur-selector.js',
        content
    )

    # Commenter le bloc des event listeners du dropdown
    content = re.sub(
        r'(const dropdownToggle = document\.getElementById\(\'coach-dropdown-toggle\'\);.*?}\s+})',
        lambda m: '\n      // Event listeners désactivés - gérés par entrepreneur-selector.js\n      /*\n      ' + m.group(1).replace('\n', '\n      ') + '\n      */',
        content,
        flags=re.DOTALL
    )

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Event listeners commentés")
    else:
        print(f"○ Aucun changement")

print("\n" + "="*60)
print("Désactivation des event listeners inline terminée!")
print("="*60)
