import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# HTML structure to add (from avis.html)
SELECTOR_HTML = '''<!-- Backdrop overlay -->
<div id="coach-selector-backdrop"></div>

<!-- Coach Entrepreneur Selector -->
<div id="coach-entrepreneur-selector">
  <!-- Identité de la page (icône et nom) -->
  <div class="page-identity">
    <div class="page-icon">
      <i class="fas fa-file-invoice-dollar"></i>
    </div>
    <div class="page-name">Facturation QE</div>
  </div>

  <!-- Titre et sous-titre (visibles uniquement en mode centré) -->
  <div class="selector-title">
    <i class="fas fa-user-tie"></i>
    Sélectionnez un entrepreneur
  </div>
  <div class="selector-subtitle">Choisissez l'entrepreneur dont vous souhaitez consulter les factures</div>

  <div class="selector-container">
    <div class="selector-label">
      <i class="fas fa-user-tie"></i>
      <span>Entrepreneur:</span>
    </div>
    <div class="coach-dropdown">
      <div class="coach-dropdown-toggle" id="coach-dropdown-toggle">
        <span class="placeholder">-- Sélectionner un entrepreneur --</span>
        <i class="fas fa-chevron-down chevron"></i>
      </div>
      <div class="coach-dropdown-menu" id="coach-dropdown-menu">
        <!-- Options chargées dynamiquement -->
      </div>
    </div>
  </div>
</div>

'''

file_path = r'QE\Frontend\Entrepreneurs\Gestions\Facturation QE\Facturation QE.html'

print(f"\n{'='*60}")
print(f"Adding selector HTML to: {file_path}")
print('='*60)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

original = content

# Check if selector HTML already exists
if 'id="coach-entrepreneur-selector"' in content:
    print("✓ Selector HTML already exists")
else:
    # Find where the </head> tag is, so we can add after <body>
    # We need to find <body> or where the content starts
    # Look for common patterns like <div id="page1" or first <div after </head>

    # Find </head> first
    head_end_match = re.search(r'</head>\s*(<body[^>]*>)?', content, re.IGNORECASE)

    if head_end_match:
        # Find the position right after </head> and optional <body>
        insert_pos = head_end_match.end()

        # Insert the selector HTML at this position
        content = content[:insert_pos] + '\n' + SELECTOR_HTML + '\n' + content[insert_pos:]

        print("✓ Added selector HTML after </head> tag")
    else:
        print("✗ Could not find </head> tag")

if content != original:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ File updated: {file_path}")
else:
    print(f"○ No changes made")

print("\n" + "="*60)
print("Script completed!")
print("="*60)
