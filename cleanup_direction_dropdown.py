import re

file_path = r'QE\Frontend\Entrepreneurs\Gestions\Employes\gestionemployes.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remove the direction dropdown HTML container
direction_html_pattern = r'<div class="direction-dropdown-container"[^>]*>.*?</div>\s*</div>\s*</div>'
content = re.sub(direction_html_pattern, '', content, flags=re.DOTALL)

# 2. Remove the direction dropdown CSS
direction_css_pattern = r'/\* Dropdown Entrepreneur pour Direction \*/\s*\.direction-dropdown-container\s*\{[^}]*\}.*?\.direction-dropdown-option:active\s*\{[^}]*\}'
content = re.sub(direction_css_pattern, '', content, flags=re.DOTALL)

# 3. Remove the direction dropdown JavaScript (the DOMContentLoaded block we added)
direction_js_pattern = r'// ==================== ENTREPRENEUR DROPDOWN FOR DIRECTION ONLY ====================\s*document\.addEventListener\(\'DOMContentLoaded\', function\(\) \{.*?loadEntrepreneursForDirection\(\);\s*\}\);'
content = re.sub(direction_js_pattern, '', content, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Nettoyage termine - dropdown direction supprime")
