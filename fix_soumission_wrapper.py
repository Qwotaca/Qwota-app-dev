#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Lire le fichier soumission.html
with open('QE/Frontend/Entrepreneurs/Outils/Soumission/soumission.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Remplacer #main-content par #main-content-wrapper dans le script anti-flash
content = content.replace(
    '          #main-content {',
    '          #main-content-wrapper {'
)

# 2. Remplacer le div id="main-content" par id="main-content-wrapper"
content = content.replace(
    '<div id="main-content">',
    '<div id="main-content-wrapper">'
)

# 3. Remplacer le padding-top pour body.has-selection #main-content
content = content.replace(
    '    body.has-selection #main-content {',
    '    body.has-selection #main-content-wrapper {'
)

# Écrire le fichier modifié
with open('QE/Frontend/Entrepreneurs/Outils/Soumission/soumission.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Soumission corrigée: main-content → main-content-wrapper!")
