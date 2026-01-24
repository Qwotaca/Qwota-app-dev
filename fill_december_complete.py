"""
Script pour remplir COMPLETEMENT toutes les semaines de decembre 2025
avec donnees RPO + resume (probleme, focus, rating)
"""
import json
import os

def fill_complete_december():
    """Remplit toutes les semaines avec donnees completes"""
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
    if '12' not in data['weekly']:
        data['weekly']['12'] = {}

    # Donnees COMPLETES pour chaque semaine (metriques + resume)
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
            'satisfaction': 4.3,
            'probleme': 'Difficulte a obtenir des rendez-vous en debut de mois',
            'focus': 'Ameliorer le script de prise de contact telephonique',
            'rating': 3
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
            'satisfaction': 4.5,
            'probleme': 'Taux de conversion estimations/contrats un peu faible',
            'focus': 'Travailler la presentation et le closing',
            'rating': 4
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
            'satisfaction': 4.7,
            'probleme': 'Gestion du temps avec premier peintre embauche',
            'focus': 'Optimiser la planification et delegation',
            'rating': 5
        },
        '4': {  # Semaine 22-28 dec (semaine internationale)
            'h_marketing': 13.0,
            'estimation': 11,
            'contract': 3,
            'dollar': 5500,
            'depot': 1300,
            'peintre': 0,
            'ca_cumul': 21000,
            'produit': 3800,
            'prod_horaire': 295,
            'satisfaction': 4.6,
            'probleme': 'Periode des fetes, moins de disponibilite clients',
            'focus': 'Maximiser les heures de prospection malgre les fetes',
            'rating': 4
        },
        '5': {  # Semaine 29-31 dec
            'h_marketing': 6.0,
            'estimation': 5,
            'contract': 1,
            'dollar': 2500,
            'depot': 600,
            'peintre': 0,
            'ca_cumul': 23500,
            'produit': 1500,
            'prod_horaire': 250,
            'satisfaction': 4.5,
            'probleme': 'Fin d\'annee, semaine courte et vacances',
            'focus': 'Preparer la rentree de janvier',
            'rating': 3
        }
    }

    # Remplir toutes les semaines
    for week, week_data in weeks_data.items():
        data['weekly']['12'][week] = week_data
        print(f"  Semaine {week}: {week_data['h_marketing']}h PAP, {week_data['estimation']} est., {week_data['dollar']}$ | Resume: {week_data['rating']}/5 etoiles")

    # Sauvegarder
    with open(rpo_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nOK - Toutes les semaines de decembre 2025 COMPLETEMENT remplies")
    print(f"   Fichier: {rpo_file}")
    print(f"   Inclus: metriques + probleme + focus + rating pour chaque semaine")
    print(f"   Rechargez la page et le modal devrait disparaitre!")

if __name__ == "__main__":
    fill_complete_december()
