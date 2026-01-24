"""
Script pour remplir toutes les semaines de decembre 2025 avec des donnees RPO pour mathis
"""
import json
import os

def fill_december_rpo():
    """Remplit toutes les semaines de decembre avec des donnees realistes"""
    username = 'mathis'
    rpo_file = f'cloud/rpo/{username}_rpo.json'

    # Creer le dossier si necessaire
    os.makedirs('cloud/rpo', exist_ok=True)

    # Charger les donnees existantes ou creer un nouveau fichier
    if os.path.exists(rpo_file):
        with open(rpo_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            'username': username,
            'weekly': {}
        }

    # Decembre 2025 = mois 12
    # Semaines de decembre:
    # Semaine 1: 1-7 dec
    # Semaine 2: 8-14 dec
    # Semaine 3: 15-21 dec
    # Semaine 4: 22-28 dec
    # Semaine 5: 29-31 dec (partielle)

    if '12' not in data['weekly']:
        data['weekly']['12'] = {}

    # Donnees pour chaque semaine
    weeks_data = {
        '1': {  # Semaine 1-7 dec
            'h_marketing': 10.5,
            'estimation': 8,
            'contract': 2,
            'dollar': 3500,
            'depot': 800,
            'peintre': 0,
            'ca_cumul': 3500,
            'produit': 2000,
            'prod_horaire': 190,
            'satisfaction': 4.3
        },
        '2': {  # Semaine 8-14 dec
            'h_marketing': 12.0,
            'estimation': 10,
            'contract': 3,
            'dollar': 5200,
            'depot': 1200,
            'peintre': 0,
            'ca_cumul': 8700,
            'produit': 3500,
            'prod_horaire': 292,
            'satisfaction': 4.5
        },
        '3': {  # Semaine 15-21 dec
            'h_marketing': 14.0,
            'estimation': 12,
            'contract': 4,
            'dollar': 6800,
            'depot': 1500,
            'peintre': 1,
            'ca_cumul': 15500,
            'produit': 4200,
            'prod_horaire': 300,
            'satisfaction': 4.7
        },
        '4': {  # Semaine 22-28 dec (semaine internationale - quest 1)
            'h_marketing': 13.0,  # Plus que 12h pour completer la quest
            'estimation': 11,
            'contract': 3,
            'dollar': 5500,
            'depot': 1300,
            'peintre': 0,
            'ca_cumul': 21000,
            'produit': 3800,
            'prod_horaire': 295,
            'satisfaction': 4.6
        },
        '5': {  # Semaine 29-31 dec (partielle)
            'h_marketing': 6.0,
            'estimation': 5,
            'contract': 1,
            'dollar': 2500,
            'depot': 600,
            'peintre': 0,
            'ca_cumul': 23500,
            'produit': 1500,
            'prod_horaire': 250,
            'satisfaction': 4.5
        }
    }

    # Remplir toutes les semaines
    for week, week_data in weeks_data.items():
        data['weekly']['12'][week] = week_data
        print(f"  Semaine {week}: {week_data['h_marketing']}h PAP, {week_data['estimation']} estimations, {week_data['dollar']}$")

    # Sauvegarder
    with open(rpo_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nOK - Toutes les semaines de decembre 2025 remplies pour {username}")
    print(f"   Fichier: {rpo_file}")
    print(f"   Rechargez la page gamification pour voir vos donnees!")

if __name__ == "__main__":
    fill_december_rpo()
