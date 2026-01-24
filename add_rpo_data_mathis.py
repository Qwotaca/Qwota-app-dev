"""
Script pour ajouter des donnees RPO pour mathis afin de completer la premiere quest
"""
import json
import os

def add_rpo_data():
    """Ajoute des donnees RPO pour completer la premiere quest"""
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

    # La premiere quest: "Faire 12h de PAP durant la semaine Internationale"
    # Deadline: 2025-12-25 (dimanche)
    # Semaine: 19 dec au 25 dec 2025
    # Lundi: 19 dec 2025
    # Cette semaine correspond a decembre (mois 12), probablement semaine 3 ou 4

    # Ajouter les donnees pour decembre, semaine 4 (semaine du 19-25 dec)
    if '12' not in data['weekly']:
        data['weekly']['12'] = {}

    if '4' not in data['weekly']['12']:
        data['weekly']['12']['4'] = {}

    # Ajouter 12h de PAP pour completer la quest
    data['weekly']['12']['4']['h_marketing'] = 12.0
    data['weekly']['12']['4']['estimation'] = 0
    data['weekly']['12']['4']['contract'] = 0
    data['weekly']['12']['4']['dollar'] = 0
    data['weekly']['12']['4']['depot'] = 0
    data['weekly']['12']['4']['peintre'] = 0
    data['weekly']['12']['4']['ca_cumul'] = 0
    data['weekly']['12']['4']['produit'] = 0
    data['weekly']['12']['4']['prod_horaire'] = 0
    data['weekly']['12']['4']['satisfaction'] = 0

    # Sauvegarder
    with open(rpo_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"OK - Donnees RPO ajoutees pour {username}")
    print(f"   12h de PAP pour la semaine du 19-25 dec 2025")
    print(f"   Fichier: {rpo_file}")
    print(f"   Rechargez la page gamification pour voir le streak!")

if __name__ == "__main__":
    add_rpo_data()
