import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = [
    r'QE\Frontend\Entrepreneurs\Gestions\Employes\gestionemployes.html',
    r'QE\Frontend\Entrepreneurs\Gestions\Ventes\Ventes.html',
    r'QE\Frontend\Entrepreneurs\General\RPO\rpo.html',
    r'QE\Frontend\Entrepreneurs\Gestions\Facturation QE\Facturation QE.html',
    r'QE\Frontend\Entrepreneurs\Gestions\Avis\avis.html',
]

old_toggle = '''<div class="coach-dropdown-toggle" id="coach-dropdown-toggle">
          <span class="placeholder">-- Sélectionner un entrepreneur --</span>
          <i class="fas fa-chevron-down chevron"></i>
        </div>'''

new_toggle = '''<div class="coach-dropdown-toggle" id="coach-dropdown-toggle">
          <input type="text"
                 class="search-input"
                 id="search-input"
                 placeholder="-- Sélectionner un entrepreneur --"
                 autocomplete="off"
                 readonly>
          <span class="placeholder">-- Sélectionner un entrepreneur --</span>
          <i class="fas fa-chevron-down chevron"></i>
        </div>'''

for file_path in files:
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print('='*60)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        if old_toggle in content:
            content = content.replace(old_toggle, new_toggle)
            print("✓ Toggle modifié")
        else:
            print("○ Toggle déjà modifié ou introuvable")

        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Fichier mis à jour")
        else:
            print(f"○ Aucun changement")

    except FileNotFoundError:
        print(f"✗ Fichier non trouvé: {file_path}")

print("\n" + "="*60)
print("Modification terminée!")
print("="*60)
