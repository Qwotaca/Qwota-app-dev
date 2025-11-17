# Structure des badges

Ce dossier contient toutes les images des badges organisées par type et rareté.

## Structure des dossiers

```
badges/
├── fleur/
│   ├── commun/
│   ├── rare/
│   ├── epique/
│   ├── legendaire/
│   └── mythique/
├── etoile/
│   ├── commun/
│   ├── rare/
│   ├── epique/
│   ├── legendaire/
│   └── mythique/
├── trophee/
│   ├── commun/
│   ├── rare/
│   ├── epique/
│   ├── legendaire/
│   └── mythique/
└── badge/
    ├── commun/
    ├── rare/
    ├── epique/
    ├── legendaire/
    └── mythique/
```

## Nomenclature des fichiers

Les images doivent être nommées selon le badge_id défini dans `gamification.py`.

**Exemples:**
- `premiere_vente.png` → Badge "Première Vente"
- `victoire.png` → Badge "Victoire"
- `formation_base.png` → Badge "Formation de base"

## Format des images

- Format: PNG avec transparence
- Taille recommandée: 512x512 pixels
- Fond transparent

## Utilisation dans le code

Les badges sont chargés automatiquement via l'URL:
```
/static/badges/{type}/{rareté}/{badge_id}.png
```

**Exemple:**
```
/static/badges/fleur/commun/premiere_vente.png
```

## Déploiement

Ces fichiers sont servis statiquement via FastAPI et fonctionnent automatiquement en production (GitHub, serveur, etc.) grâce au mount `/static` dans `main.py`.
