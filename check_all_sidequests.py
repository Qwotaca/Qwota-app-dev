"""
Script pour afficher la progression de TOUTES les side quests de l'année
Logs formatés avec préfixe [SIDEQUEST]
"""

from QE.Backend.rpo import load_user_rpo_data, get_week_number_from_date
from datetime import datetime, timedelta

# Définition de TOUTES les side quests de l'année (même structure que gamification.html)
WEEKLY_QUESTS = [
    {"title": "Faire 12h de PAP durant la semaine Internationale", "deadline": "2026-01-12", "target": 12, "unit": "heures"},
    {"title": "Faire 12h de PAP durant la semaine", "deadline": "2026-01-19", "target": 12, "unit": "heures"},
    {"title": "Faire 12h de PAP durant la semaine", "deadline": "2026-01-26", "target": 12, "unit": "heures"},
    {"title": "Faire 3 estimations ou plus cette semaine", "deadline": "2026-02-02", "target": 3, "unit": "estimations"},
    {"title": "Avoir un taux marketing de 0,75 estimations par heure", "deadline": "2026-02-09", "target": 0.75, "unit": "taux"},
    {"title": "Faire 5 estimations cette semaine", "deadline": "2026-02-16", "target": 5, "unit": "estimations"},
    {"title": "Faire 5 estimations cette semaine", "deadline": "2026-02-23", "target": 5, "unit": "estimations"},
    {"title": "Faire 7 estimations cette semaine", "deadline": "2026-03-02", "target": 7, "unit": "estimations"},
    {"title": "Signer 5000$", "deadline": "2026-03-09", "target": 5000, "unit": "$"},
    {"title": "Collecter plus de 1500$ en dépôt", "deadline": "2026-03-16", "target": 1500, "unit": "depot"},
    {"title": "Signer 7500$", "deadline": "2026-03-23", "target": 7500, "unit": "$"},
    {"title": "Signer un contrat de plus de 4000$ avant taxes", "deadline": "2026-03-30", "target": 4000, "unit": "$"},
    {"title": "Profiter de la folie de Pâques pour signer 15000$ cette semaine", "deadline": "2026-04-06", "target": 15000, "unit": "$"},
    {"title": "Embaucher un premier peintre", "deadline": "2026-04-13", "target": 1, "unit": "peintre"},
    {"title": "Signer 10000$", "deadline": "2026-04-20", "target": 10000, "unit": "$"},
    {"title": "Signer 12000$", "deadline": "2026-04-27", "target": 12000, "unit": "$"},
    {"title": "Signer 12000$", "deadline": "2026-05-04", "target": 12000, "unit": "$"},
    {"title": "Signer 12000$", "deadline": "2026-05-11", "target": 12000, "unit": "$"},
    {"title": "Signer 12000$", "deadline": "2026-05-18", "target": 12000, "unit": "$"},
    {"title": "15 estimations cette semaine", "deadline": "2026-05-25", "target": 15, "unit": "estimations"},
    {"title": "Atteindre 100000$ de ventes cumulatif depuis le début de l'année", "deadline": "2026-06-01", "target": 100000, "unit": "ca_cumul"},
    {"title": "Produire 5000$ de contrats", "deadline": "2026-06-08", "target": 5000, "unit": "produit"},
    {"title": "Productivité horaire de plus de 90", "deadline": "2026-06-15", "target": 90, "unit": "productivité"},
    {"title": "Faire 10h de PAP cette semaine", "deadline": "2026-06-22", "target": 10, "unit": "heures"},
    {"title": "Faire plus de 15 estimations cette semaine", "deadline": "2026-06-29", "target": 15, "unit": "estimations"},
    {"title": "Productivité horaire de plus de 100", "deadline": "2026-07-06", "target": 100, "unit": "productivité"},
    {"title": "Produire 15000$ cette semaine", "deadline": "2026-07-13", "target": 15000, "unit": "produit"},
    {"title": "Satisfaction client cumulative de plus de 4,5 étoiles", "deadline": "2026-07-20", "target": 4.5, "unit": "étoiles"},
    {"title": "10 estimations cette semaine", "deadline": "2026-07-27", "target": 10, "unit": "estimations"},
    {"title": "Signer 5000$", "deadline": "2026-08-03", "target": 5000, "unit": "$"},
    {"title": "Productivité horaire de 110", "deadline": "2026-08-10", "target": 110, "unit": "productivité"},
    {"title": "Produire 10000$", "deadline": "2026-08-17", "target": 10000, "unit": "produit"},
    {"title": "Produire 10000$", "deadline": "2026-08-24", "target": 10000, "unit": "produit"},
    {"title": "Faire 9h de PAP", "deadline": "2026-09-28", "target": 9, "unit": "heures"},
    {"title": "Signer 5000$", "deadline": "2026-10-05", "target": 5000, "unit": "$"},
    {"title": "Signer 10000$", "deadline": "2026-10-12", "target": 10000, "unit": "$"},
    {"title": "Signer 10000$", "deadline": "2026-10-19", "target": 10000, "unit": "$"},
    {"title": "Signer 5000$", "deadline": "2026-10-26", "target": 5000, "unit": "$"},
]


def check_quest_progress(username, quest, quest_num):
    """Vérifie la progression d'une side quest"""

    try:
        # Calculer le lundi de la semaine
        deadline = datetime.strptime(quest['deadline'], '%Y-%m-%d')
        monday = deadline - timedelta(days=6)
        monday_str = monday.strftime('%Y-%m-%d')

        # Formater les dates pour affichage
        monday_display = monday.strftime('%d %b')
        deadline_display = deadline.strftime('%d %b %Y')

        # Mapper au RPO
        month_idx, week_num = get_week_number_from_date(monday_str)

        # Charger les données RPO
        rpo_data = load_user_rpo_data(username)
        week_data = rpo_data.get('weekly', {}).get(str(month_idx), {}).get(str(week_num), {})

        # Extraire les métriques selon le type de quest
        h_marketing = week_data.get('h_marketing', '-')
        estimation = week_data.get('estimation', 0)
        contract = week_data.get('contract', 0)
        dollar = week_data.get('dollar', 0)
        depot = week_data.get('depot', 0)
        peintre = week_data.get('peintre', 0)
        ca_cumul = week_data.get('ca_cumul', 0)
        produit = week_data.get('produit', 0)
        prod_horaire = week_data.get('prod_horaire', 0)
        satisfaction = week_data.get('satisfaction', 0)

        # Convertir h_marketing en nombre
        try:
            h_marketing_num = float(h_marketing) if h_marketing != '-' else 0
        except:
            h_marketing_num = 0

        # Calculer le taux marketing de la semaine
        taux_marketing = 0
        if h_marketing_num > 0:
            taux_marketing = round(estimation / h_marketing_num, 2)

        # Déterminer la progression selon le type
        current_progress = 0
        unit_display = quest['unit']

        if quest['unit'] == 'heures':
            current_progress = h_marketing_num
            unit_display = 'h'
        elif quest['unit'] == 'estimations':
            current_progress = estimation
            unit_display = 'est.'
        elif quest['unit'] == '$':
            current_progress = dollar
            unit_display = '$'
        elif quest['unit'] == 'depot':
            current_progress = depot
            unit_display = '$'
        elif quest['unit'] == 'peintre':
            current_progress = peintre
            unit_display = 'peintre(s)'
        elif quest['unit'] == 'ca_cumul':
            current_progress = ca_cumul
            unit_display = '$'
        elif quest['unit'] == 'produit':
            current_progress = produit
            unit_display = '$'
        elif quest['unit'] == 'taux':
            current_progress = taux_marketing
            unit_display = 'est/h'
        elif quest['unit'] == 'productivité':
            current_progress = prod_horaire
            unit_display = '$/h'
        elif quest['unit'] == 'étoiles':
            current_progress = satisfaction
            unit_display = 'étoiles'
        elif quest['unit'] == 'contrats':
            current_progress = contract
            unit_display = 'contrats'

        # Calculer le pourcentage
        target = quest['target']
        percent = (current_progress / target * 100) if target > 0 else 0

        # Déterminer le statut
        if percent >= 100:
            status = "[OK] COMPLETEE"
            status_emoji = "[+++]"
        elif percent >= 75:
            status = "[>>] PRESQUE"
            status_emoji = "[++]"
        elif percent >= 50:
            status = "[->] EN COURS"
            status_emoji = "[+]"
        elif percent > 0:
            status = "[..] DEBUT"
            status_emoji = "[.]"
        else:
            status = "[--] PAS COMMENCE"
            status_emoji = "[-]"

        # Affichage formaté
        print(f"\n[SIDEQUEST #{quest_num:02d}] {status_emoji} {quest['title']}")
        print(f"[SIDEQUEST #{quest_num:02d}] Periode: {monday_display} - {deadline_display}")
        print(f"[SIDEQUEST #{quest_num:02d}] Progression: {current_progress:.1f}/{target} {unit_display} ({percent:.1f}%)")
        print(f"[SIDEQUEST #{quest_num:02d}] Statut: {status}")

        # Afficher les détails de la semaine
        print(f"[SIDEQUEST #{quest_num:02d}] Details RPO (Mois {month_idx}, Semaine {week_num}):")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Heures PAP: {h_marketing_num}h")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Estimations: {estimation}")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Contrats: {contract}")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Dollars: {dollar:.0f}$")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Depots: {depot:.0f}$")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Peintres: {peintre}")
        print(f"[SIDEQUEST #{quest_num:02d}]    - CA Cumulatif: {ca_cumul:.0f}$")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Produit: {produit:.0f}$")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Taux marketing: {taux_marketing:.2f} est/h")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Productivite horaire: {prod_horaire:.0f}$/h")
        print(f"[SIDEQUEST #{quest_num:02d}]    - Satisfaction: {satisfaction:.2f} etoiles")

        return {
            'completed': percent >= 100,
            'percent': percent,
            'current': current_progress,
            'target': target
        }

    except Exception as e:
        print(f"\n[SIDEQUEST #{quest_num:02d}] ❌ ERREUR: {str(e)}")
        return {'completed': False, 'percent': 0, 'current': 0, 'target': quest['target']}


def main():
    """Fonction principale"""
    username = 'mathis'  # Changez si besoin

    print("=" * 80)
    print(f"[SIDEQUEST] ANALYSE COMPLETE DES SIDE QUESTS - ANNEE 2026")
    print(f"[SIDEQUEST] Utilisateur: {username.upper()}")
    print(f"[SIDEQUEST] Date: {datetime.now().strftime('%d %B %Y %H:%M')}")
    print("=" * 80)

    total_quests = len(WEEKLY_QUESTS)
    completed_quests = 0
    total_progress = 0
    quest_results = []

    # Analyser chaque quest
    for i, quest in enumerate(WEEKLY_QUESTS, 1):
        result = check_quest_progress(username, quest, i)
        quest_results.append(result)
        if result['completed']:
            completed_quests += 1
        total_progress += result['percent']

    # Calculer le streak
    today = datetime.now()
    streak = 0
    for i, quest in enumerate(WEEKLY_QUESTS):
        deadline = datetime.strptime(quest['deadline'], '%Y-%m-%d')
        # Si la deadline est dans le futur, on arrête
        if deadline > today:
            break
        # Si complétée, on incrémente le streak, sinon on reset
        if quest_results[i]['completed']:
            streak += 1
        else:
            streak = 0

    # Statistiques globales
    avg_progress = total_progress / total_quests if total_quests > 0 else 0

    print("\n" + "=" * 80)
    print(f"[SIDEQUEST] STATISTIQUES GLOBALES")
    print("=" * 80)
    print(f"[SIDEQUEST] Total de quests: {total_quests}")
    print(f"[SIDEQUEST] Quests completees: {completed_quests}/{total_quests} ({completed_quests/total_quests*100:.1f}%)")
    print(f"[SIDEQUEST] Progression moyenne: {avg_progress:.1f}%")
    print(f"[SIDEQUEST] Score de completion: {completed_quests}/{total_quests}")
    print(f"[SIDEQUEST] Streak actuel: {streak} quests consecutives")
    print("=" * 80)

    # Trouver la quest actuelle (prochaine dans le futur)
    today = datetime.now()
    current_quest = None
    for i, quest in enumerate(WEEKLY_QUESTS, 1):
        deadline = datetime.strptime(quest['deadline'], '%Y-%m-%d')
        if deadline > today:
            current_quest = (i, quest)
            break

    if current_quest:
        print(f"\n[SIDEQUEST] QUEST ACTIVE ACTUELLE:")
        print(f"[SIDEQUEST] -> Quest #{current_quest[0]:02d}: {current_quest[1]['title']}")
        print(f"[SIDEQUEST] -> Deadline: {current_quest[1]['deadline']}")
    else:
        print(f"\n[SIDEQUEST] TOUTES LES QUESTS SONT TERMINEES!")

    print("\n")


if __name__ == "__main__":
    main()
