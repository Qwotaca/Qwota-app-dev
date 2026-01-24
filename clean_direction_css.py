import re

file_path = r'QE\Frontend\Entrepreneurs\Gestions\Employes\gestionemployes.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Supprimer tout le CSS direction-dropdown (lignes 1850-1981 environ)
pattern = r'\.direction-dropdown-container \{.*?\.direction-dropdown-option i \{\s*color: var\(--primary-blue\);\s*font-size: 1\.1rem;\s*\}'

content = re.sub(pattern, '', content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("CSS direction-dropdown supprime")
