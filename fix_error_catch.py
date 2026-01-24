import re
import os

files_to_fix = [
    'QE/Frontend/Entrepreneurs/Outils/GQP/gqp.html',
    'QE/Frontend/Entrepreneurs/Gestions/Employes/gestionemployes.html',
    'QE/Frontend/Entrepreneurs/Gestions/Ventes/Ventes.html'
]

for file_path in files_to_fix:
    if not os.path.exists(file_path):
        print(f'File not found: {file_path}')
        continue

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Remplacer catch (error) par catch (err)
    content = re.sub(r'\bcatch\s*\(\s*error\s*\)', 'catch (err)', content)

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed: {file_path}')
    else:
        print(f'No changes: {file_path}')

print('Done!')
