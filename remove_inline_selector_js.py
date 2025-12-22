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

    # Pattern to find the inline selector script block:
    # Starts with <script> followed by the comment "// Gestion du sélecteur d'entrepreneur"
    # Ends with the closing </script>

    pattern = r'<script>\s*//\s*Gestion du sélecteur d\'entrepreneur.*?</script>'

    matches = list(re.finditer(pattern, content, re.DOTALL))

    if matches:
        for match in matches:
            print(f"  Found inline selector script at position {match.start()}-{match.end()}")
            # Replace with a comment
            content = content.replace(
                match.group(0),
                '<!-- Inline entrepreneur selector script removed - now handled by shared /entrepreneur-selector.js -->',
                1
            )
    else:
        print(f"  No inline selector script found")

    # Clean up multiple blank lines
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ JavaScript inline supprimé")
    else:
        print(f"○ Aucun changement")

print("\n" + "="*60)
print("Nettoyage JavaScript inline terminé!")
print("="*60)
