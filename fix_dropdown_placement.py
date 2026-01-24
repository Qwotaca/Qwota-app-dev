import re
import sys
import io

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read the file
with open(r'QE\Frontend\Entrepreneurs\Gestions\Employes\gestionemployes.html', 'r', encoding='utf-8') as f:
    content = f.read()

# First, find and extract the dropdown HTML that was added after <body>
dropdown_pattern = r'(<div class="direction-dropdown-container".*?</div>\s*</div>\s*</div>)'
dropdown_match = re.search(dropdown_pattern, content, re.DOTALL)

if dropdown_match:
    dropdown_html = dropdown_match.group(1)

    # Remove it from after <body>
    content = content.replace(dropdown_html, '')

    # Find the main-content div and insert the dropdown right after it
    main_content_pattern = r'(<div class="main-content w-full"[^>]*>)'

    def insert_dropdown(match):
        return match.group(1) + '\n\n  ' + dropdown_html + '\n'

    content = re.sub(main_content_pattern, insert_dropdown, content)

    # Write back
    with open(r'QE\Frontend\Entrepreneurs\Gestions\Employes\gestionemployes.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print("OK - Moved dropdown inside main-content container")
else:
    print("ERROR - Dropdown HTML not found")
