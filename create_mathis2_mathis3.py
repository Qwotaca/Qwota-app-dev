import sqlite3
import json
import os
from datetime import datetime
import bcrypt

def create_new_entrepreneurs():
    """Crée les comptes mathis2 et mathis3 comme de nouveaux entrepreneurs"""

    # Password par défaut: mathis123
    password_hash = bcrypt.hashpw("mathis123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Connexion à la base de données
    conn = sqlite3.connect('data/qwota.db')
    cursor = conn.cursor()

    # Récupérer l'ID de coach3
    cursor.execute("SELECT id FROM users WHERE username = ?", ('coach3',))
    coach3_result = cursor.fetchone()
    if not coach3_result:
        print("[ERREUR] Coach3 n'existe pas dans la base de donnees!")
        return
    coach3_id = coach3_result[0]

    for username in ['mathis2', 'mathis3']:
        print(f"\n=== Creation de l'utilisateur {username} ===")

        # 1. Supprimer l'utilisateur s'il existe déjà dans la DB
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        print(f"[OK] Utilisateur {username} supprime de la DB (si existant)")

        # 2. Créer l'utilisateur dans la DB
        current_time = datetime.now().isoformat()
        email = f"{username}@qwota.com"
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, coach_id, email, created_at, is_active, onboarding_completed, videos_completed)
            VALUES (?, ?, 'entrepreneur', ?, ?, ?, 1, 0, 0)
        """, (username, password_hash, coach3_id, email, current_time))
        print(f"[OK] Utilisateur {username} cree dans la DB avec coach3")

        # 3. Créer le fichier account JSON
        account_data = {
            "username": username,
            "role": "entrepreneur",
            "password": password_hash,
            "assigned_coach": "coach3"
        }
        os.makedirs('data/accounts', exist_ok=True)
        with open(f'data/accounts/{username}.json', 'w', encoding='utf-8') as f:
            json.dump(account_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Fichier account cree: data/accounts/{username}.json")

        # 4. Créer le fichier RPO vide
        rpo_data = {
            "username": username,
            "year_2025": {
                "hrpap_vise": 0,
                "estimation_vise": 0,
                "contract_vise": 0,
                "dollar_vise": 0,
                "vente_vise": 30,
                "moyen_vise": 2500,
                "tendance_vise": 440000,
                "ratio_mktg": 85,
                "cm_prevision": 2500,
                "taux_vente": 30,
                "objectif_pap": 0,
                "objectif_rep": 0,
                "hr_pap_reel": 0,
                "estimation_reel": 0,
                "contract_reel": 0,
                "dollar_reel": 0,
                "mktg_reel": 0,
                "vente_reel": 0,
                "moyen_reel": 0,
                "prod_horaire": 0
            },
            "monthly": {
                "dec2025": {
                    "obj_pap": 0,
                    "obj_rep": 0,
                    "hrpap_vise": 0,
                    "estimation_vise": 0,
                    "contract_vise": 0,
                    "dollar_vise": 0,
                    "vente_vise": 0,
                    "moyen_vise": 0,
                    "weeks": {}
                }
            },
            "last_updated": datetime.now().isoformat(),
            "etats_resultats": {
                "budget_percent": {},
                "actuel": {},
                "budget": {}
            }
        }

        # Ajouter les semaines de décembre 2025
        weeks = [
            {"week_num": "1", "week_label": "1 - 7 déc"},
            {"week_num": "2", "week_label": "8 - 14 déc"},
            {"week_num": "3", "week_label": "15 - 21 déc"},
            {"week_num": "4", "week_label": "22 - 28 déc"},
            {"week_num": "5", "week_label": "29 déc - 4 janv"}
        ]

        for week in weeks:
            rpo_data["monthly"]["dec2025"]["weeks"][week["week_num"]] = {
                "h_marketing": "-",
                "estimation": 0,
                "contract": 0,
                "dollar": 0,
                "prod_horaire": 0,
                "rating": 0,
                "commentaire": "Problème: - | Focus: -"
            }

        os.makedirs('data/rpo', exist_ok=True)
        with open(f'data/rpo/{username}_rpo.json', 'w', encoding='utf-8') as f:
            json.dump(rpo_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] Fichier RPO cree: data/rpo/{username}_rpo.json")

        # 5. Créer les dossiers vides pour les données
        folders = [
            f'data/prospects/{username}',
            f'data/ventes_attente/{username}',
            f'data/ventes_acceptees/{username}',
            f'data/ventes_produit/{username}',
            f'data/reviews/{username}',
            f'data/signatures/{username}',
            f'data/soumissions_completes/{username}',
            f'data/soumissions_signees/{username}',
            f'data/employes/{username}'
        ]

        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        print(f"[OK] Dossiers crees pour {username}")

        # 6. Créer les fichiers JSON vides
        json_files = {
            f'data/prospects/{username}/prospects.json': [],
            f'data/ventes_attente/{username}/ventes_attente.json': [],
            f'data/ventes_acceptees/{username}/ventes_acceptees.json': [],
            f'data/ventes_produit/{username}/ventes.json': [],
            f'data/reviews/{username}/reviews.json': [],
            f'data/soumissions_completes/{username}/soumissions.json': [],
            f'data/soumissions_signees/{username}/soumissions_signees.json': [],
            f'data/employes/{username}/employes.json': []
        }

        for filepath, content in json_files.items():
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"[OK] Fichiers JSON vides crees pour {username}")

        print(f"\n[SUCCESS] {username} cree avec succes!")
        print(f"   Username: {username}")
        print(f"   Password: mathis123")
        print(f"   Role: entrepreneur")
        print(f"   Coach assigne: coach3")

    # Sauvegarder les changements
    conn.commit()
    conn.close()

    print("\n" + "="*60)
    print("[SUCCESS] mathis2 et mathis3 crees comme nouveaux comptes")
    print("="*60)
    print("\nInformations de connexion:")
    print("  - mathis2 / mathis123")
    print("  - mathis3 / mathis123")
    print("  - Coach assigne: coach3")

if __name__ == "__main__":
    create_new_entrepreneurs()
