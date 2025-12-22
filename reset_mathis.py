"""
Script pour reset complètement le compte mathis
- Garde: bypass onboarding, vidéos du guide
- Reset: RPO, ventes, soumissions, projets, stats, gamification, etc.
"""
import os
import json
import shutil
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")

USERNAME = "mathis"

print(f"[RESET] Reset du compte: {USERNAME}")
print("=" * 60)

# Liste de tous les dossiers à nettoyer pour mathis
folders_to_clean = [
    # Ventes
    ("ventes_attente", USERNAME),
    ("ventes_acceptees", USERNAME),
    ("ventes_produit", USERNAME),

    # Soumissions
    ("soumissions_completes", USERNAME),
    ("soumissions_signees", USERNAME),

    # RPO
    ("rpo", USERNAME),

    # Projets
    ("projets", USERNAME),
    ("projects", USERNAME),
    ("travaux_a_completer", USERNAME),
    ("travaux_completes", USERNAME),

    # GQP
    ("gqp", USERNAME),

    # Stats et dashboard
    ("stats", USERNAME),
    ("dashboard", USERNAME),

    # Facturation
    ("factures_completes", USERNAME),
    ("facturation_qe_historique", USERNAME),
    ("facturation_qe_statuts", USERNAME),
    ("facturations_en_cours", USERNAME),
    ("facturations_traitees", USERNAME),
    ("facturations_urgentes", USERNAME),
    ("soumission_signee_facturation_qe", USERNAME),

    # Autres
    ("clients_perdus", USERNAME),
    ("total_signees", USERNAME),
    ("reviews", USERNAME),
    ("chiffre_affaires", USERNAME),
    ("remboursements", USERNAME),
]

cleaned_count = 0
error_count = 0

# Nettoyer tous les dossiers
for parent_folder, subfolder in folders_to_clean:
    path = os.path.join(DATA_DIR, parent_folder, subfolder)

    if os.path.exists(path):
        try:
            # Supprimer tout le contenu
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

            print(f"[OK] Nettoye: {parent_folder}/{subfolder}")
            cleaned_count += 1
        except Exception as e:
            print(f"[ERROR] Erreur sur {parent_folder}/{subfolder}: {e}")
            error_count += 1
    else:
        print(f"[WARN] N'existe pas: {parent_folder}/{subfolder}")

print("\n" + "=" * 60)

# Reset gamification (badges, XP, niveau)
try:
    db_path = os.path.join(DATA_DIR, "gamification.db")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Reset XP et niveau
        cursor.execute("""
            UPDATE users
            SET xp = 0, niveau = 1
            WHERE username = ?
        """, (USERNAME,))

        # Supprimer tous les badges
        cursor.execute("""
            DELETE FROM user_badges
            WHERE username = ?
        """, (USERNAME,))

        # Supprimer tout l'historique XP
        cursor.execute("""
            DELETE FROM xp_history
            WHERE username = ?
        """, (USERNAME,))

        conn.commit()
        conn.close()

        print(f"[OK] Gamification reset (XP=0, Niveau=1, 0 badges)")
    else:
        print("[WARN] gamification.db n'existe pas")
except Exception as e:
    print(f"[ERROR] Erreur gamification: {e}")
    error_count += 1

print("=" * 60)

# NE PAS TOUCHER à:
print("\n[PRESERVE] PRESERVE (pas touche):")
print("  - Bypass onboarding (parametres utilisateur)")
print("  - Videos du guide")
print("  - Compte utilisateur (username/password)")
print("  - Tokens Gmail/Calendar")
print("  - Signatures")

print("\n" + "=" * 60)
print(f"[OK] Dossiers nettoyes: {cleaned_count}")
print(f"[ERROR] Erreurs: {error_count}")
print(f"[SUCCESS] Reset du compte '{USERNAME}' termine!")
print("=" * 60)
