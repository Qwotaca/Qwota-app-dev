"""
Script pour créer des badges de base (cercles colorés)
Style: Jeu vidéo animé, propre, coloré
"""

from PIL import Image, ImageDraw
import os

# Couleurs par rareté (style gaming)
RARITY_COLORS = {
    'Commun': {
        'main': (129, 140, 248),      # Indigo
        'glow': (165, 180, 252),      # Indigo clair
        'dark': (79, 70, 229)          # Indigo foncé
    },
    'Rare': {
        'main': (96, 165, 250),        # Bleu
        'glow': (147, 197, 253),       # Bleu clair
        'dark': (37, 99, 235)          # Bleu foncé
    },
    'Légendaire': {
        'main': (251, 191, 36),        # Or
        'glow': (253, 224, 71),        # Or clair
        'dark': (245, 158, 11)         # Or foncé
    },
    'Mythique': {
        'main': (244, 114, 182),       # Rose
        'glow': (251, 207, 232),       # Rose clair
        'dark': (219, 39, 119)         # Rose foncé
    },
    'Épique': {
        'main': (167, 139, 250),       # Violet
        'glow': (196, 181, 253),       # Violet clair
        'dark': (124, 58, 237)         # Violet foncé
    },
    'Anti-Badge': {
        'main': (248, 113, 113),       # Rouge
        'glow': (254, 202, 202),       # Rouge clair
        'dark': (220, 38, 38)          # Rouge foncé
    }
}

def create_badge_base(rarity, output_path, size=512):
    """
    Crée un badge de base (cercle avec effet glow)

    Args:
        rarity: Rareté du badge (Commun, Rare, Légendaire, etc.)
        output_path: Chemin où sauvegarder l'image
        size: Taille de l'image (défaut 512x512)
    """
    # Créer image transparente
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    colors = RARITY_COLORS.get(rarity, RARITY_COLORS['Commun'])
    center = size // 2

    # Effet glow externe (plusieurs cercles avec opacité décroissante)
    for i in range(5):
        glow_size = center - 20 - (i * 5)
        alpha = 30 - (i * 5)
        glow_color = colors['glow'] + (alpha,)

        draw.ellipse(
            [center - glow_size, center - glow_size,
             center + glow_size, center + glow_size],
            fill=glow_color
        )

    # Cercle principal
    main_radius = center - 50
    draw.ellipse(
        [center - main_radius, center - main_radius,
         center + main_radius, center + main_radius],
        fill=colors['main'] + (255,)
    )

    # Reflet/highlight en haut
    highlight_radius = main_radius - 30
    highlight_offset = -main_radius // 3
    draw.ellipse(
        [center - highlight_radius, center + highlight_offset - highlight_radius,
         center + highlight_radius, center + highlight_offset + highlight_radius],
        fill=colors['glow'] + (80,)
    )

    # Bordure brillante
    border_radius = main_radius + 5
    draw.ellipse(
        [center - border_radius, center - border_radius,
         center + border_radius, center + border_radius],
        outline=colors['glow'] + (200,),
        width=3
    )

    # Ombre interne en bas
    shadow_radius = main_radius - 40
    shadow_offset = main_radius // 4
    draw.ellipse(
        [center - shadow_radius, center + shadow_offset - shadow_radius,
         center + shadow_radius, center + shadow_offset + shadow_radius],
        fill=colors['dark'] + (40,)
    )

    # Sauvegarder
    img.save(output_path, 'PNG')
    print(f"✓ Badge créé: {output_path}")

def create_all_flower_badges():
    """
    Crée tous les badges fleur de base
    """
    # Créer dossier de sortie
    output_dir = "badges_fleurs"
    os.makedirs(output_dir, exist_ok=True)

    # Définition des badges avec leur rareté
    badges = [
        # Communs
        ("victoire", "Commun"),
        ("costumier", "Commun"),
        ("pagayeurs", "Commun"),
        ("ho_ho_ho", "Commun"),

        # Rares
        ("mvp", "Rare"),
        ("mention_semaine", "Rare"),
        ("thermometre_plein", "Rare"),
        ("note_peintres", "Rare"),
        ("vikings", "Rare"),
        ("eleve_parfait", "Rare"),
        ("formations", "Rare"),
        ("retour", "Rare"),

        # Légendaires
        ("champions", "Légendaire"),
        ("entrepreneur_semaine", "Légendaire"),
        ("pool_facile", "Légendaire"),
        ("mvp_presidents", "Légendaire"),
        ("president", "Légendaire"),
        ("referen_coeurs", "Légendaire"),
        ("referenceur", "Légendaire"),
        ("peintres_entrepreneur", "Légendaire"),
        ("qe_coeur", "Légendaire"),
        ("premier_classe", "Légendaire"),

        # Mythiques
        ("encore_president", "Mythique"),
        ("elite", "Mythique"),
        ("modele_peintres", "Mythique"),
        ("ad_vitam", "Mythique"),
        ("qe_vie", "Mythique"),
        ("coach", "Mythique"),
        ("mentor", "Mythique"),

        # Épiques
        ("president_toujours", "Épique"),
        ("elite_elite", "Épique"),
        ("super_coach", "Épique"),
        ("berceuse", "Épique"),

        # Anti-Badges
        ("evenement_manque", "Anti-Badge"),
        ("compta_pas_faite", "Anti-Badge"),
    ]

    print("🎨 Création des badges fleur...\n")

    for badge_name, rarity in badges:
        output_path = os.path.join(output_dir, f"{badge_name}.png")
        create_badge_base(rarity, output_path)

    print(f"\n✅ {len(badges)} badges créés dans le dossier '{output_dir}/'")
    print("\nProchaine étape: Importer dans Figma/Photoshop pour ajouter les détails (fleurs, icônes, etc.)")

if __name__ == "__main__":
    # Exemple: créer un seul badge
    print("Exemple: Création d'un badge Légendaire...")
    create_badge_base("Légendaire", "exemple_legendaire.png")

    # Créer tous les badges
    print("\n" + "="*50)
    response = input("\nCréer tous les badges fleur? (o/n): ")
    if response.lower() == 'o':
        create_all_flower_badges()
