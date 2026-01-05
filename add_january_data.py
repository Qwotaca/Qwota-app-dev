"""
Script pour ajouter les donnees de janvier 2026 dans le RPO
Inclut 40h pour la semaine 3 (12-18 janvier) pour completer la quest #2
"""
import json

def add_january_data():
    """Ajoute les donnees de janvier 2026"""
    username = 'mathis'
    rpo_file = f'cloud/rpo/{username}_rpo.json'

    # Charger les donnees existantes
    with open(rpo_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Janvier 2026 = month index 0
    if '0' not in data['weekly']:
        data['weekly']['0'] = {}

    # Donnees pour janvier 2026
    january_data = {
        '1': {  # Semaine 29 dec - 4 jan (partielle)
            'h_marketing': 5.0,
            'estimation': 4,
            'contract': 1,
            'dollar': 2000,
            'depot': 500,
            'peintre': 0,
            'ca_cumul': 25500,
            'produit': 1200,
            'prod_horaire': 240,
            'satisfaction': 4.2,
            'probleme': 'Reprise apres les fetes, motivation a retrouver',
            'focus': 'Reprendre le rythme progressivement',
            'rating': 3
        },
        '2': {  # Semaine 5-11 janvier
            'h_marketing': 11.0,
            'estimation': 9,
            'contract': 2,
            'dollar': 4200,
            'depot': 1000,
            'peintre': 0,
            'ca_cumul': 29700,
            'produit': 2800,
            'prod_horaire': 255,
            'satisfaction': 4.4,
            'probleme': 'Prospection difficile en debut d\'annee',
            'focus': 'Intensifier les appels et le porte-a-porte',
            'rating': 4
        },
        '3': {  # Semaine 12-18 janvier - QUEST #2!
            'h_marketing': 40.0,  # 40 heures! Largement suffisant pour les 12h requis
            'estimation': 32,
            'contract': 8,
            'dollar': 18500,
            'depot': 4200,
            'peintre': 1,
            'ca_cumul': 48200,
            'produit': 12000,
            'prod_horaire': 300,
            'satisfaction': 4.8,
            'probleme': 'Tres forte charge de travail avec 40h de marketing',
            'focus': 'Maintenir le rythme et optimiser les conversions',
            'rating': 5
        },
        '4': {  # Semaine 19-25 janvier
            'h_marketing': 12.5,
            'estimation': 10,
            'contract': 3,
            'dollar': 6500,
            'depot': 1500,
            'peintre': 0,
            'ca_cumul': 54700,
            'produit': 4200,
            'prod_horaire': 280,
            'satisfaction': 4.6,
            'probleme': 'Fatigue apres la semaine intense precedente',
            'focus': 'Recuperer tout en maintenant la performance',
            'rating': 4
        }
    }

    # Ajouter toutes les semaines
    for week, week_data in january_data.items():
        data['weekly']['0'][week] = week_data
        print(f"  Semaine {week}: {week_data['h_marketing']}h PAP, {week_data['estimation']} estimations, {week_data['dollar']}$")

    # Sauvegarder
    with open(rpo_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nOK - Donnees de janvier 2026 ajoutees!")
    print(f"   Fichier: {rpo_file}")
    print(f"\n   IMPORTANT:")
    print(f"   - Semaine 3 (12-18 jan): 40h de PAP!")
    print(f"   - Quest #2 completee (40h > 12h requis)")
    print(f"   - Avec quest #1 (dec), vous avez maintenant un STREAK DE 2!")

if __name__ == "__main__":
    add_january_data()
