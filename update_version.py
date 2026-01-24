#!/usr/bin/env python3
"""
Script pour mettre à jour la version de l'application
Cela déclenchera une notification de mise à jour chez tous les clients connectés
"""

import json
import os
from datetime import datetime, timezone

VERSION_FILE = "version.json"

def update_version(new_version=None):
    """
    Met à jour le fichier version.json avec une nouvelle version
    Si new_version n'est pas fourni, seul le timestamp est mis à jour
    """
    # Charger la version actuelle
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
    else:
        version_data = {
            "version": "1.0.0",
            "lastUpdate": datetime.now(timezone.utc).isoformat()
        }

    # Mettre à jour la version si fournie
    if new_version:
        version_data["version"] = new_version

    # Toujours mettre à jour le timestamp
    version_data["lastUpdate"] = datetime.now(timezone.utc).isoformat()

    # Sauvegarder
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(version_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Version mise à jour!")
    print(f"   Version: {version_data['version']}")
    print(f"   Dernière mise à jour: {version_data['lastUpdate']}")
    print(f"\n🔔 Tous les clients connectés recevront une notification de mise à jour dans les 30 secondes.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Version spécifiée en argument
        new_version = sys.argv[1]
        update_version(new_version)
    else:
        # Seulement mettre à jour le timestamp (déclenchera quand même la notification)
        print("[NOTE] Déclenchement d'une mise à jour (sans changement de numéro de version)")
        update_version()
