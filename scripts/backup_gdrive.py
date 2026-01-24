#!/usr/bin/env python3
"""
Script de backup automatique vers Google Drive
Lance manuellement: python scripts/backup_gdrive.py
"""

import os
import subprocess
from datetime import datetime

# Configuration
RCLONE_REMOTE = "gdrive:Backups_Render"
BACKUP_SOURCE = "/mnt/cloud"
KEEP_DAYS = 7  # Garder les backups des 7 derniers jours

def setup_rclone():
    """Configure rclone si pas déjà fait"""
    rclone_config = os.path.expanduser("~/.config/rclone/rclone.conf")

    if os.path.exists(rclone_config):
        print("[OK] rclone déjà configuré")
        return True

    # Créer le dossier config
    os.makedirs(os.path.dirname(rclone_config), exist_ok=True)

    # Config rclone depuis les variables d'environnement
    client_id = os.getenv("GDRIVE_CLIENT_ID", "")
    client_secret = os.getenv("GDRIVE_CLIENT_SECRET", "")
    token = os.getenv("GDRIVE_TOKEN", "")

    if not all([client_id, client_secret, token]):
        print("[ERREUR] Variables d'environnement GDRIVE_* manquantes")
        return False

    config_content = f"""[gdrive]
type = drive
client_id = {client_id}
client_secret = {client_secret}
scope = drive
token = {token}
team_drive =
"""

    with open(rclone_config, 'w') as f:
        f.write(config_content)

    print("[OK] rclone configuré")
    return True


def install_rclone():
    """Installe rclone si pas présent"""
    # Vérifier si rclone est disponible
    result = subprocess.run(["which", "rclone"], capture_output=True)
    if result.returncode == 0:
        print("[OK] rclone déjà installé")
        return "rclone"

    # Télécharger rclone
    home = os.path.expanduser("~")
    rclone_dir = os.path.join(home, "rclone")
    rclone_bin = os.path.join(rclone_dir, "rclone")

    if os.path.exists(rclone_bin):
        print("[OK] rclone trouvé dans ~/rclone")
        return rclone_bin

    print("[INFO] Installation de rclone...")
    os.makedirs(rclone_dir, exist_ok=True)

    subprocess.run([
        "curl", "-L",
        "https://downloads.rclone.org/rclone-current-linux-amd64.zip",
        "-o", f"{home}/rclone.zip"
    ], check=True)

    subprocess.run(["unzip", "-o", f"{home}/rclone.zip", "-d", home], check=True)

    # Trouver le dossier extrait
    for item in os.listdir(home):
        if item.startswith("rclone-") and item.endswith("-linux-amd64"):
            extracted_dir = os.path.join(home, item)
            subprocess.run(["cp", f"{extracted_dir}/rclone", rclone_bin], check=True)
            break

    print("[OK] rclone installé")
    return rclone_bin


def run_backup():
    """Exécute le backup"""
    print("=" * 50)
    print(f"BACKUP - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Vérifier qu'on est sur Linux (production)
    if os.name != 'posix' or not os.path.exists(BACKUP_SOURCE):
        print(f"[SKIP] Pas en production ou {BACKUP_SOURCE} n'existe pas")
        return False

    # Installer/trouver rclone
    rclone = install_rclone()

    # Configurer rclone
    if not setup_rclone():
        return False

    # Créer le backup
    date_str = datetime.now().strftime("%Y-%m-%d_%H%M")
    backup_file = f"/tmp/backup_{date_str}.tar.gz"

    print(f"[INFO] Création du backup: {backup_file}")
    result = subprocess.run(
        ["tar", "-czf", backup_file, "-C", BACKUP_SOURCE, "."],
        capture_output=True
    )

    if result.returncode != 0:
        print(f"[ERREUR] tar: {result.stderr.decode()}")
        return False

    # Taille du backup
    size_mb = os.path.getsize(backup_file) / (1024 * 1024)
    print(f"[OK] Backup créé: {size_mb:.1f} MB")

    # Upload sur Google Drive
    print(f"[INFO] Upload vers {RCLONE_REMOTE}...")
    result = subprocess.run(
        [rclone, "copy", backup_file, RCLONE_REMOTE, "-P"],
        capture_output=True
    )

    if result.returncode != 0:
        print(f"[ERREUR] rclone: {result.stderr.decode()}")
        return False

    print("[OK] Upload terminé")

    # Supprimer le fichier temporaire
    os.remove(backup_file)
    print("[OK] Fichier temporaire supprimé")

    # Supprimer les vieux backups (> 7 jours)
    print(f"[INFO] Nettoyage des backups > {KEEP_DAYS} jours...")
    subprocess.run(
        [rclone, "delete", RCLONE_REMOTE, "--min-age", f"{KEEP_DAYS}d"],
        capture_output=True
    )
    print("[OK] Nettoyage terminé")

    print("=" * 50)
    print("BACKUP TERMINÉ AVEC SUCCÈS")
    print("=" * 50)
    return True


if __name__ == "__main__":
    run_backup()
