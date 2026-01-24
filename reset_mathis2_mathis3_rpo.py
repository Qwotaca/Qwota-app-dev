import json
from datetime import datetime

def reset_rpo_to_zero(username):
    """Reset complètement le RPO d'un utilisateur à 0"""

    rpo_path = f'data/rpo/{username}_rpo.json'

    # Structure RPO complètement à 0
    rpo_data = {
        "username": username,
        "year_2025": {
            "hrpap_vise": 0,
            "estimation_vise": 0,
            "contract_vise": 0,
            "dollar_vise": 0,
            "vente_vise": 0,
            "moyen_vise": 0,
            "tendance_vise": 0,
            "ratio_mktg": 0,
            "cm_prevision": 0,
            "taux_vente": 0,
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
                "weeks": {
                    "1": {
                        "h_marketing": "-",
                        "estimation": 0,
                        "contract": 0,
                        "dollar": 0,
                        "prod_horaire": 0,
                        "rating": 0,
                        "commentaire": "Problème: - | Focus: -"
                    },
                    "2": {
                        "h_marketing": "-",
                        "estimation": 0,
                        "contract": 0,
                        "dollar": 0,
                        "prod_horaire": 0,
                        "rating": 0,
                        "commentaire": "Problème: - | Focus: -"
                    },
                    "3": {
                        "h_marketing": "-",
                        "estimation": 0,
                        "contract": 0,
                        "dollar": 0,
                        "prod_horaire": 0,
                        "rating": 0,
                        "commentaire": "Problème: - | Focus: -"
                    },
                    "4": {
                        "h_marketing": "-",
                        "estimation": 0,
                        "contract": 0,
                        "dollar": 0,
                        "prod_horaire": 0,
                        "rating": 0,
                        "commentaire": "Problème: - | Focus: -"
                    },
                    "5": {
                        "h_marketing": "-",
                        "estimation": 0,
                        "contract": 0,
                        "dollar": 0,
                        "prod_horaire": 0,
                        "rating": 0,
                        "commentaire": "Problème: - | Focus: -"
                    }
                }
            }
        },
        "last_updated": datetime.now().isoformat(),
        "etats_resultats": {
            "budget_percent": {},
            "actuel": {
                "assurance-qe": 0,
                "concours": 0,
                "essence": 0,
                "entretien-voiture": 0,
                "fourniture-bureau": 0,
                "frais-bancaires": 0,
                "frais-cellulaire": 0,
                "frais-garanties": 0,
                "leads": 0,
                "peinture": 0,
                "petits-outils": 0,
                "repas": 0,
                "redevances": 0,
                "salaire-peintres": 0,
                "salaires-representant": 0
            },
            "budget": {}
        },
        "annual": {
            "objectif_ca": 0,
            "hrpap_vise": 0,
            "estimation_vise": 0,
            "contract_vise": 0,
            "dollar_vise": 0,
            "mktg_vise": 0,
            "vente_vise": 0,
            "moyen_vise": 0,
            "tendance_vise": 0,
            "ratio_mktg": 0,
            "cm_prevision": 0,
            "taux_vente": 0,
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
        }
    }

    # Écrire le fichier
    with open(rpo_path, 'w', encoding='utf-8') as f:
        json.dump(rpo_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] RPO de {username} reset a 0")

if __name__ == "__main__":
    print("=== Reset RPO mathis2 et mathis3 a 0 ===\n")

    reset_rpo_to_zero('mathis2')
    reset_rpo_to_zero('mathis3')

    print("\n[SUCCESS] RPO de mathis2 et mathis3 completement resets a 0")
    print("Tous les dashboards devraient maintenant afficher 0 pour ces utilisateurs")
