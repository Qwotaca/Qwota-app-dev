"""
Script pour renommer les badges étoiles numérotés vers leurs vrais noms
"""
import os
import shutil

# Mapping: numéro -> nom de fichier
MAPPING = {
    # COMMUN
    "39": "maitre_estimateur",
    "40": "droit_passage",
    "41": "producteur",
    "42": "paneliste_debutant",
    "43": "droit_peinture",
    "44": "annee_2_parti",
    "45": "pret_an_2",
    "46": "valet_formateur",

    # RARE
    "47": "super_producteur",
    "48": "paneliste_agguerri",
    "49": "grosse_annee",
    "50": "grafiti",
    "51": "dame_formateur",

    # ÉPIQUE
    "61": "recrutement_niveau_3",
    "62": "former_releve_2",
    "63": "conferencier_expert_3",

    # LÉGENDAIRE
    "52": "maitre_producteur",
    "53": "paneliste_expert",
    "54": "annee_record",
    "55": "roi_formateur",
    "56": "recrutement_expert_1",
    "57": "coaching_expert_1",
    "58": "conferencier_expert_1",
    "59": "coach_terrain_expert_1",
    "60": "formateur_prod_expert_1",

    # MYTHIQUE
    "64": "roi_production",
    "65": "roi_panel",
    "66": "meilleur_panel_senior",
    "67": "recrutement_expert_2",
    "68": "organisateur_expert_1",
    "69": "coaching_expert_2",
    "70": "conferencier_expert_2",
    "71": "formateur_prod_expert_2",
    "72": "former_releve_1",
}

RARETE_FOLDERS = {
    "commun": ["39", "40", "41", "42", "43", "44", "45", "46"],
    "rare": ["47", "48", "49", "50", "51"],
    "epique": ["61", "62", "63"],
    "legendaire": ["52", "53", "54", "55", "56", "57", "58", "59", "60"],
    "mythique": ["64", "65", "66", "67", "68", "69", "70", "71", "72"],
}

base_dir = os.path.dirname(__file__)
badges_dir = os.path.join(base_dir, "static", "badges", "etoile")

print("Renommage des badges etoiles...")
print()

total_renamed = 0

for rarete, numeros in RARETE_FOLDERS.items():
    folder = os.path.join(badges_dir, rarete)
    print(f"[{rarete.upper()}]:")

    for num in numeros:
        old_name = f"{num}.png"
        new_name = f"{MAPPING[num]}.png"

        old_path = os.path.join(folder, old_name)
        new_path = os.path.join(folder, new_name)

        if os.path.exists(old_path):
            shutil.move(old_path, new_path)
            print(f"   OK {old_name} -> {new_name}")
            total_renamed += 1
        else:
            print(f"   MANQUANT {old_name}")

    print()

print(f"SUCCES: {total_renamed} badges renommes!")
