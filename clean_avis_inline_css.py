import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

file_path = r'QE\Frontend\Entrepreneurs\Gestions\Avis\avis.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# Supprimer tout le CSS inline du coach-entrepreneur-selector
# On cherche depuis le premier #coach-entrepreneur-selector jusqu'à body.coach-mode
pattern = r'#coach-entrepreneur-selector\s*\{.*?body\.coach-mode\s*>\s*div:not\(#coach-entrepreneur-selector\):not\(\.mobile-overlay\)\s*\{[^}]*\}'

content = re.sub(pattern, '', content, flags=re.DOTALL)

# Nettoyer les lignes vides
content = re.sub(r'\n{3,}', '\n\n', content)

if content != original:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ CSS inline supprimé de avis.html")
else:
    print("○ Aucun changement")
