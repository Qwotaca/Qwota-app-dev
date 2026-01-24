import re

files_to_fix = [
    'QE/Frontend/Entrepreneurs/Outils/GQP/gqp.html',
    'QE/Frontend/Entrepreneurs/Gestions/Employes/gestionemployes.html',
    'QE/Frontend/Entrepreneurs/Gestions/Ventes/Ventes.html'
]

for file_path in files_to_fix:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_catch_block = False
    modified = False

    for i, line in enumerate(lines):
        # Détecter le début d'un bloc catch (err)
        if 'catch (err)' in line:
            in_catch_block = True
            continue

        # Si on est dans un bloc catch, remplacer error(..., error) par error(..., err)
        if in_catch_block and 'error(' in line:
            # Remplacer le second "error" (celui passé comme paramètre) par "err"
            # Pattern: error('message', error) -> error('message', err)
            new_line = re.sub(r"error\('([^']*)',\s*error\)", r"error('\1', err)", line)
            new_line = re.sub(r'error\("([^"]*)",\s*error\)', r'error("\1", err)', new_line)
            new_line = re.sub(r"error\(`([^`]*)\`,\s*error\)", r"error(`\1`, err)", new_line)

            if new_line != line:
                lines[i] = new_line
                modified = True

        # Fin du bloc catch (détection approximative avec les accolades)
        if in_catch_block and line.strip().startswith('}'):
            in_catch_block = False

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f'Fixed error usage in: {file_path}')
    else:
        print(f'No error usage to fix in: {file_path}')

print('Done!')
