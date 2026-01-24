"""
Script pour corriger l'index de mois pour decembre 2025
Le systeme utilise month_index = -2 pour decembre 2025, pas 12!
"""
import json
import os

def fix_month_index():
    """Corrige l'index de mois de 12 a -2 pour decembre 2025"""
    username = 'mathis'
    rpo_file = f'cloud/rpo/{username}_rpo.json'

    # Charger les donnees
    with open(rpo_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Copier les donnees de mois "12" vers "-2"
    if '12' in data['weekly']:
        data['weekly']['-2'] = data['weekly']['12']
        del data['weekly']['12']  # Supprimer l'ancien index
        print("OK - Donnees deplacees de l'index 12 vers -2")
    elif '-2' in data['weekly']:
        print("OK - Les donnees sont deja a l'index -2")
    else:
        print("ATTENTION - Aucune donnee trouvee pour decembre")

    # Sauvegarder
    with open(rpo_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Fichier mis a jour: {rpo_file}")
    print("Structure finale:")
    print(f"  Mois -2 (dec 2025): {len(data['weekly'].get('-2', {}))} semaines")
    print("Rechargez la page - le modal devrait disparaitre!")

if __name__ == "__main__":
    fix_month_index()
