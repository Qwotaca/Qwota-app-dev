"""
Script pour renommer automatiquement les images de badges fleurs
selon leur rareté et les badge_id de BADGES_CONFIG
"""
import os
import shutil
from pathlib import Path

# Chemin de base
BASE_DIR = Path(__file__).parent / "static" / "badges" / "fleur"

# Mapping des badges par rareté (depuis BADGES_CONFIG)
BADGES_PAR_RARETE = {
    "commun": [
        "victoire_jitqe",
        "costumier",
        "pagayeurs",
        "ho_ho_ho"
    ],
    "rare": [
        "mvp_competition",
        "mention_semaine",
        "thermometre_plein",
        "retour_2",
        "note_peintres",
        "vikings",
        "eleve_parfait",
        "formations"
    ],
    "epique": [
        "president_3",
        "elite_2",
        "super_coach",
        "berceuse"
    ],
    "legendaire": [
        "champions_jitqe",
        "entrepreneur_semaine",
        "pool_facile",
        "mvp_presidents",
        "president_1",
        "referencoeurs",
        "referenceurs",
        "peintre_entrepreneur",
        "retour_3",
        "premier_classe"
    ],
    "mythique": [
        "president_2",
        "elite_1",
        "modele_peintres",
        "retour_4",
        "retour_5",
        "coach",
        "mentor"
    ]
}

def renommer_badges():
    """Renomme toutes les images de badges selon leur rareté"""

    print("[DEBUT] Renommage des badges fleurs...\n")

    total_renommes = 0

    for rarete, badge_ids in BADGES_PAR_RARETE.items():
        dossier = BASE_DIR / rarete

        if not dossier.exists():
            print(f"[WARNING] Dossier {rarete} n'existe pas, creation...")
            dossier.mkdir(parents=True, exist_ok=True)
            continue

        # Lister toutes les images PNG dans le dossier
        images = sorted([f for f in dossier.glob("*.png")])

        print(f"[{rarete.upper()}]")
        print(f"   Images trouvées: {len(images)}")
        print(f"   Badges attendus: {len(badge_ids)}")

        if len(images) == 0:
            print(f"   [WARNING] Aucune image a renommer\n")
            continue

        if len(images) > len(badge_ids):
            print(f"   [WARNING] Plus d'images que de badges! Seules les {len(badge_ids)} premieres seront renommees\n")
        elif len(images) < len(badge_ids):
            print(f"   [WARNING] Il manque {len(badge_ids) - len(images)} images!\n")

        # Renommer chaque image
        for i, image in enumerate(images):
            if i >= len(badge_ids):
                print(f"   [SKIP] Image supplementaire ignoree: {image.name}")
                continue

            nouveau_nom = f"{badge_ids[i]}.png"
            nouveau_chemin = dossier / nouveau_nom

            # Si le fichier existe déjà avec le bon nom, skip
            if image.name == nouveau_nom:
                print(f"   [OK] {image.name} (deja correct)")
                continue

            # Si un fichier avec le nouveau nom existe déjà, le sauvegarder temporairement
            if nouveau_chemin.exists():
                temp_name = dossier / f"temp_{nouveau_nom}"
                nouveau_chemin.rename(temp_name)
                print(f"   [BACKUP] Sauvegarde temporaire: {nouveau_nom} -> temp_{nouveau_nom}")

            # Renommer
            try:
                image.rename(nouveau_chemin)
                print(f"   [OK] {image.name} -> {nouveau_nom}")
                total_renommes += 1
            except Exception as e:
                print(f"   [ERROR] Erreur lors du renommage de {image.name}: {e}")

        print()

    print(f"\n[SUCCESS] Renommage termine! {total_renommes} fichiers renommes.")
    print("\n[INFO] Badges manquants:")

    # Vérifier les badges manquants
    for rarete, badge_ids in BADGES_PAR_RARETE.items():
        dossier = BASE_DIR / rarete
        for badge_id in badge_ids:
            fichier = dossier / f"{badge_id}.png"
            if not fichier.exists():
                print(f"   [MISSING] {rarete}/{badge_id}.png")

if __name__ == "__main__":
    try:
        renommer_badges()
    except Exception as e:
        print(f"\n[ERROR] ERREUR: {e}")
        import traceback
        traceback.print_exc()

    input("\nAppuyez sur Entrée pour fermer...")
