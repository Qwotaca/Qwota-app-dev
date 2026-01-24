import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

files = [
    r'QE\Frontend\Entrepreneurs\Gestions\Facturation QE\Facturation QE.html',
    r'QE\Frontend\Entrepreneurs\Gestions\Avis\avis.html',
]

for file_path in files:
    print(f"\n{'='*60}")
    print(f"Processing: {file_path}")
    print('='*60)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Strategy: Find and remove the specific loadEntrepreneursForCoach function
    # Look for: async function loadEntrepreneursForCoach() { ... }
    # This function typically has fetch calls and DOM manipulation

    # Pattern 1: Remove the async function loadEntrepreneursForCoach
    # We'll match from "async function loadEntrepreneursForCoach" to its closing brace
    # Looking for balanced braces

    pattern = r'async\s+function\s+loadEntrepreneursForCoach\s*\([^)]*\)\s*\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
    matches = list(re.finditer(pattern, content, re.DOTALL))

    if matches:
        for match in matches:
            print(f"  Found loadEntrepreneursForCoach function at position {match.start()}-{match.end()}")
            content = content.replace(match.group(0), '\n      // loadEntrepreneursForCoach removed - handled by shared script\n', 1)

    # Pattern 2: Remove calls to loadEntrepreneursForCoach();
    content = re.sub(
        r'(\s*)loadEntrepreneursForCoach\s*\(\s*\)\s*;',
        r'\1// loadEntrepreneursForCoach() removed - handled by shared script',
        content
    )

    # Pattern 3: Remove event listener setup for dropdown toggle/menu (if exists)
    # Look for patterns like: const dropdownToggle = document.getElementById('coach-dropdown-toggle');
    # followed by event listeners

    # This is complex, so let's be selective:
    # Remove blocks that start with "const dropdownToggle" and end at the closing of event listeners
    # We'll match: const dropdownToggle... addEventListener... });

    pattern_dropdown = r'const\s+dropdownToggle\s*=\s*document\.getElementById\([\'"]coach-dropdown-toggle[\'"]\);.*?}\s*\}\s*\);'
    matches_dropdown = list(re.finditer(pattern_dropdown, content, re.DOTALL))

    if matches_dropdown:
        for match in matches_dropdown:
            print(f"  Found dropdown event listener setup at position {match.start()}-{match.end()}")
            content = content.replace(match.group(0), '\n      // Dropdown event listeners removed - handled by shared script\n', 1)

    # Pattern 4: Remove the selectEntrepreneur function if exists inline
    pattern_select = r'function\s+selectEntrepreneur\s*\([^)]*\)\s*\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
    matches_select = list(re.finditer(pattern_select, content, re.DOTALL))

    if matches_select:
        for match in matches_select:
            print(f"  Found selectEntrepreneur function at position {match.start()}-{match.end()}")
            content = content.replace(match.group(0), '\n      // selectEntrepreneur removed - handled by shared script\n', 1)

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
