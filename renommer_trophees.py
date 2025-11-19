"""
Script pour renommer les badges trophees numerotes vers leurs vrais noms
"""
import os
import shutil

# Mapping: numero -> nom de fichier
MAPPING = {
    # COMMUN (4 trophees)
    "73": "cap_six_chiffres",
    "74": "sprint_vente",
    "75": "operation_10k",
    "76": "chef_meute",

    # RARE (6 trophees)
    "67": "ascension",
    "68": "semaine_feu",
    "69": "roue_production",
    "70": "triple",
    "71": "bande_organisee",
    "72": "coup_fusil",

    # EPIQUE (3 trophees)
    "40": "club_million",
    "41": "goat_recrue",
    "42": "goat",

    # LEGENDAIRE (11 trophees)
    "56": "palier_titans",
    "57": "explosion_peinture",
    "58": "machine_guerre",
    "59": "etoile_montante",
    "60": "finaliste_excellence",
    "61": "chouchou",
    "62": "top_closer",
    "63": "coup_canon",
    "64": "travaillant",
    "65": "propulsion",
    "66": "collegue_or",

    # MYTHIQUE (13 trophees) - Seulement 13 images
    "43": "demi_millionnaire",
    "44": "mode_legendaire",
    "45": "maitre_peintre",
    "46": "roty",
    "47": "visionnaire",
    "48": "favori",
    "49": "big_5",
    "50": "perseverant",
    "51": "consultant_or",
    "52": "modele_tous",
    "53": "mentor_mentors",
    "54": "make_it_rain",
    "55": "madness",
}

RARETE_FOLDERS = {
    "commun": ["73", "74", "75", "76"],
    "rare": ["67", "68", "69", "70", "71", "72"],
    "epique": ["40", "41", "42"],
    "legendaire": ["56", "57", "58", "59", "60", "61", "62", "63", "64", "65", "66"],
    "mythique": ["43", "44", "45", "46", "47", "48", "49", "50", "51", "52", "53", "54", "55"],
}

base_dir = os.path.dirname(__file__)
badges_dir = os.path.join(base_dir, "static", "badges", "trophee")

print("Renommage des badges trophees...")
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
