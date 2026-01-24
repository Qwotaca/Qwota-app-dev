"""
Script de migration one-shot pour ajouter/corriger datePremiereFacturation
sur tous les clients avec des paiements traités.

Utilise la vraie date du premier paiement (depot.date, paiementFinal.date, ou autresPaiements[].date)
au lieu de la date de migration.

Usage:
    python QE/Backend/migration_datePremiereFacturation.py
"""

import json
import os
import sys
from datetime import datetime

# Détection OS pour chemins de fichiers
if sys.platform == 'win32':
    base_cloud = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
else:
    base_cloud = os.getenv("STORAGE_PATH", "/mnt/cloud")

# Statuts qui indiquent qu'un paiement n'a PAS été envoyé (à ignorer)
STATUTS_NON_ENVOYES = ['non_envoye', 'refuse', None, '']


def parse_date_fr(date_str):
    """Parse date format DD/MM/YYYY to ISO format"""
    if not date_str:
        return None
    try:
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            return datetime(int(year), int(month), int(day))
    except Exception as e:
        print(f"[WARN] Erreur parsing date '{date_str}': {e}")
    return None


def is_payment_sent(statut):
    """Vérifie si un paiement a été envoyé (tout statut sauf non_envoye/refuse)"""
    return statut not in STATUTS_NON_ENVOYES


def get_first_payment_date(data):
    """
    Trouve la date du premier paiement envoyé (la plus ancienne).
    Un paiement est considéré envoyé dès qu'il a un statut autre que 'non_envoye' ou 'refuse'.
    Cherche dans depot, paiementFinal, et autresPaiements.
    """
    dates = []

    # Vérifier depot - PRIORITÉ: dès qu'il y a un depot envoyé, on prend sa date
    depot = data.get('depot', {})
    if isinstance(depot, dict) and is_payment_sent(depot.get('statut')):
        d = parse_date_fr(depot.get('date'))
        if d:
            dates.append(d)

    # Vérifier paiementFinal
    pf = data.get('paiementFinal', {})
    if isinstance(pf, dict) and is_payment_sent(pf.get('statut')):
        d = parse_date_fr(pf.get('date'))
        if d:
            dates.append(d)

    # Vérifier autresPaiements
    for ap in data.get('autresPaiements', []):
        if isinstance(ap, dict) and is_payment_sent(ap.get('statut')):
            d = parse_date_fr(ap.get('date'))
            if d:
                dates.append(d)

    # Retourner la plus ancienne date en format ISO
    if dates:
        return min(dates).isoformat()
    return None


def run_migration():
    """Exécute la migration sur tous les utilisateurs"""
    users_dir = os.path.join(base_cloud, 'facturation_qe_statuts')
    total_updated = 0
    total_users = 0

    print("=" * 70)
    print("MIGRATION: Corriger datePremiereFacturation avec vraie date du paiement")
    print("=" * 70)
    print(f"Dossier data: {base_cloud}")
    print("")

    if not os.path.exists(users_dir):
        print(f"[ERREUR] Dossier facturation_qe_statuts introuvable: {users_dir}")
        return False

    for username in os.listdir(users_dir):
        user_path = os.path.join(users_dir, username, 'statuts_clients.json')
        if not os.path.exists(user_path):
            continue

        total_users += 1

        try:
            with open(user_path, 'r', encoding='utf-8') as f:
                statuts = json.load(f)
        except Exception as e:
            print(f"[ERREUR] Lecture {user_path}: {e}")
            continue

        updated = 0
        for num, data in statuts.items():
            # Trouver la vraie date du premier paiement
            real_date = get_first_payment_date(data)

            if real_date:
                old_date = data.get('datePremiereFacturation')
                # Mettre à jour seulement si différent ou si n'existait pas
                if old_date != real_date:
                    statuts[num]['datePremiereFacturation'] = real_date
                    updated += 1
                    old_display = old_date[:10] if old_date and len(str(old_date)) > 10 else (old_date or 'N/A')
                    new_display = real_date[:10] if len(real_date) > 10 else real_date
                    print(f"  {username}/{num}: {old_display} -> {new_display}")

        if updated > 0:
            try:
                with open(user_path, 'w', encoding='utf-8') as f:
                    json.dump(statuts, f, indent=2, ensure_ascii=False)
                print(f"[{username}] {updated} client(s) mis à jour")
                total_updated += updated
            except Exception as e:
                print(f"[ERREUR] Écriture {user_path}: {e}")
        else:
            print(f"[{username}] Aucune correction nécessaire")

    print("")
    print("=" * 70)
    print(f"MIGRATION TERMINÉE: {total_updated} client(s) corrigé(s) sur {total_users} utilisateur(s)")
    print("=" * 70)

    return True


if __name__ == "__main__":
    run_migration()
