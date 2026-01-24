# 📋 Instructions pour ajouter les images des badges

## Structure des dossiers

Tous les badges sont organisés par **type** puis par **rareté**:

```
static/badges/
├── fleur/       (Badges de type fleur)
│   ├── commun/
│   ├── rare/
│   ├── epique/
│   ├── legendaire/
│   └── mythique/
├── etoile/      (Badges de type étoile - formations/certifications)
│   ├── commun/
│   ├── rare/
│   ├── epique/
│   ├── legendaire/
│   └── mythique/
├── trophee/     (Badges de type trophée)
│   ├── commun/
│   ├── rare/
│   ├── epique/
│   ├── legendaire/
│   └── mythique/
└── badge/       (Badges de type badge)
    ├── commun/
    ├── rare/
    ├── epique/
    ├── legendaire/
    └── mythique/
```

## 📝 Nomenclature des fichiers

Le nom du fichier doit correspondre EXACTEMENT au `badge_id` défini dans `gamification.py` (BADGES_CONFIG).

### Exemples de correspondance:

| Badge ID dans gamification.py | Fichier PNG à créer | Emplacement |
|-------------------------------|---------------------|-------------|
| `premiere_vente` | `premiere_vente.png` | `/static/badges/fleur/commun/` |
| `victoire` | `victoire.png` | `/static/badges/fleur/commun/` |
| `roi_soumission` | `roi_soumission.png` | `/static/badges/fleur/legendaire/` |
| `certification_fiscale` | `certification_fiscale.png` | `/static/badges/etoile/rare/` |
| `formation_base` | `formation_base.png` | `/static/badges/etoile/commun/` |

## 🎨 Spécifications des images

### Format
- **Extension:** `.png` (obligatoire)
- **Transparence:** Oui (fond transparent recommandé)
- **Compression:** PNG optimisé pour le web

### Dimensions
- **Taille recommandée:** 512x512 pixels
- **Taille minimale:** 256x256 pixels
- **Taille maximale:** 1024x1024 pixels
- **Ratio:** 1:1 (carré)

### Design
- Style cohérent avec l'identité visuelle de l'application
- Couleurs adaptées à la rareté du badge
- Détails visibles même en petit format (110x110px à l'affichage)

## 📋 Liste des badges à créer

### FLEURS (39 badges)

#### Commun (25 XP)
- [ ] `premiere_vente.png` → Première Vente
- [ ] `dix_clients.png` → 10 Clients satisfaits
- [ ] `cent_clients.png` → 100 Clients satisfaits
- [ ] `victoire.png` → Victoire (première soumission acceptée)
- [ ] `architecte.png` → Architecte (premier projet créé)
- [ ] `debutant_facture.png` → Première facture

#### Rare (50 XP)
- [ ] `cinq_ventes.png` → 5 Ventes
- [ ] `roi_soumission.png` → Roi de la soumission
- [ ] `cent_ventes.png` → 100 Ventes
- [ ] `marathonien_projet.png` → Marathonien du projet
- [ ] `mille_dollars.png` → 1000$ de CA
- [ ] `projecteur.png` → Projecteur (10 projets créés)

#### Épique (100 XP)
- [ ] `cinquante_ventes.png` → 50 Ventes
- [ ] `maitre_batisseur.png` → Maître Bâtisseur
- [ ] `cinq_mille_dollars.png` → 5000$ de CA
- [ ] `architecte_en_chef.png` → Architecte en Chef (50 projets)

#### Légendaire (200 XP)
- [ ] `roi_vente.png` → Roi de la vente
- [ ] `dix_mille_dollars.png` → 10000$ de CA
- [ ] `titan_projet.png` → Titan des projets (100 projets)

#### Mythique (500 XP)
- [ ] `empereur_commerce.png` → Empereur du commerce
- [ ] `cent_mille_dollars.png` → 100000$ de CA
- [ ] `legende_projet.png` → Légende des projets (500 projets)

### ÉTOILES (34 badges - Formations/Certifications)

#### Commun (25 XP)
- [ ] `formation_base.png` → Formation de base complétée
- [ ] `certification_peinture.png` → Certification Peinture Base
- [ ] `certification_estimation.png` → Certification Estimation Base
- [ ] etc. (voir gamification.py pour la liste complète)

### TROPHÉES (À définir)
Aucun badge trophée n'est encore défini dans BADGES_CONFIG.

### BADGES (À définir)
Aucun badge de type "badge" n'est encore défini dans BADGES_CONFIG.

## 🔧 Comment ajouter un nouveau badge

### 1. Créer l'image PNG
- Créer une image 512x512px avec fond transparent
- Respecter le style visuel de l'application
- Sauvegarder en PNG optimisé

### 2. Nommer le fichier
- Utiliser EXACTEMENT le `badge_id` de `gamification.py`
- Ajouter l'extension `.png`
- Exemple: `premiere_vente.png`

### 3. Placer dans le bon dossier
- Identifier le **type** du badge (fleur, etoile, trophee, badge)
- Identifier la **rareté** (commun, rare, epique, legendaire, mythique)
- Placer dans: `/static/badges/{type}/{rareté}/`

### 4. Vérifier l'affichage
- Recharger la page de gamification
- Le badge devrait s'afficher automatiquement
- Si l'image ne s'affiche pas, vérifier:
  - Le nom du fichier correspond exactement au badge_id
  - Le fichier est dans le bon dossier (type + rareté)
  - L'extension est bien `.png` (pas `.PNG` ou autre)

## 🚀 Déploiement

Les images sont automatiquement servies par FastAPI via:
```
app.mount("/static", StaticFiles(directory="static"), name="static")
```

Aucune configuration supplémentaire n'est nécessaire. Les images fonctionnent:
- ✅ En développement local
- ✅ En production (serveur, GitHub Pages, etc.)
- ✅ Dans l'application Electron

## 🔍 Debug

Si un badge ne s'affiche pas:

1. **Vérifier le badge_id dans la console navigateur:**
   ```javascript
   // Dans gamification.html, la console affiche les badges chargés
   console.log(allBadgesData);
   ```

2. **Vérifier le chemin généré:**
   - Ouvrir DevTools → Network
   - Chercher les requêtes 404 vers `/static/badges/`
   - Le chemin devrait être: `/static/badges/{type}/{rareté}/{badge_id}.png`

3. **Tester l'URL directement:**
   - Exemple: `http://localhost:8080/static/badges/fleur/commun/premiere_vente.png`
   - Si 404 → le fichier n'est pas au bon endroit
   - Si l'image s'affiche → problème dans le JavaScript

## 📞 Support

Pour toute question sur la structure des badges, consulter:
- `gamification.py` → Configuration BADGES_CONFIG (lignes 466-2023)
- `gamification.html` → Affichage frontend
- `main.py` → Routes API (lignes 10460-10580)
