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

    # Supprimer la fonction loadEntrepreneursForCoach et tout le code associé
    # Pattern pour trouver depuis "async function loadEntrepreneursForCoach" jusqu'à la fin de la fonction
    patterns = [
        # Pattern 1: La fonction complète avec son appel
        r'async function loadEntrepreneursForCoach\(\).*?(?=\n\s*(?:async function|function|</script>|document\.addEventListener))',
        # Pattern 2: L'appel de la fonction
        r'loadEntrepreneursForCoach\(\);',
        # Pattern 3: Event listeners du dropdown
        r'//\s*Gestion du dropdown.*?(?=\n\s*(?:async function|function|</script>|document\.addEventListener))',
        # Pattern 4: ANTI-FLASH code
        r'//\s*ANTI-FLASH.*?(?=\n\s*(?:async function|function|</script>|document\.addEventListener))',
    ]

    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    # Nettoyer les lignes vides multiples
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ JavaScript inline supprimé")
    else:
        print(f"○ Aucun changement")

print("\n" + "="*60)
print("Nettoyage JavaScript terminé!")
print("="*60)
