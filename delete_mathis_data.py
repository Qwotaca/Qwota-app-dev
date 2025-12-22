#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour supprimer TOUTES les données de l'entrepreneur 'mathis'
"""

import os
import shutil
import json

username = "mathis"

print(f"Suppression de toutes les donnees pour l'utilisateur '{username}'...\n")

# Liste des fichiers JSON à supprimer
json_files = [
    f"data/accounts/{username}.json",
    f"data/blacklist/{username}_event_ids.json",
    f"data/emails/{username}.json",
    f"data/rpo/{username}_rpo.json",
    f"data/tokens/{username}.json",
    f"data/tokens/{username}_agenda.json",
    f"data/templates/{username}_part_travaux.json",
    f"data/projets/{username}_projets.json",
    f"data/total_signees/{username}.json",
]

# Supprimer les fichiers JSON
deleted_files = 0
for filepath in json_files:
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            print(f"[OK] Supprime: {filepath}")
            deleted_files += 1
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la suppression de {filepath}: {e}")
    else:
        print(f"  (non existant: {filepath})")

# Liste des dossiers à supprimer
folders = [
    f"data/prospects/{username}",
    f"data/employes/{username}",
    f"data/ventes_attente/{username}",
    f"data/ventes_acceptees/{username}",
    f"data/ventes_produit/{username}",
    f"data/reviews/{username}",
    f"data/signatures/{username}",
    f"data/soumissions_completes/{username}",
    f"data/soumissions_signees/{username}",
]

# Supprimer les dossiers
deleted_folders = 0
for folder in folders:
    if os.path.exists(folder):
        try:
            shutil.rmtree(folder)
            print(f"[OK] Dossier supprime: {folder}")
            deleted_folders += 1
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la suppression de {folder}: {e}")
    else:
        print(f"  (dossier non existant: {folder})")

print(f"\nNettoyage termine!")
print(f"   - {deleted_files} fichiers supprimes")
print(f"   - {deleted_folders} dossiers supprimes")
print(f"\nNote: L'utilisateur '{username}' existe toujours dans la base de donnees.")
print(f"   Pour le supprimer completement, utilisez l'interface admin.")
