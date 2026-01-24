# Qwota Desktop App

Application desktop pour Qwota, créée avec Electron.

## Installation

1. Installer Node.js si ce n'est pas déjà fait: https://nodejs.org/

2. Installer les dépendances:
```bash
cd desktop-app
npm install
```

## Utilisation en développement

Pour tester l'application en mode développement:
```bash
npm start
```

## Créer le fichier .exe

Pour créer le fichier .exe distributable:
```bash
npm run build
```

Le fichier .exe sera créé dans le dossier `dist/`.

## Configuration du serveur

L'URL du serveur peut être configurée dans le fichier `server-config.json`:

```json
{
  "url": "http://127.0.0.1:8080"
}
```

**Important:** Si vous voulez distribuer l'application à des utilisateurs distants, vous devez:

1. Changer l'URL dans `server-config.json` pour pointer vers votre serveur accessible publiquement
   - Par exemple: `"url": "https://votre-serveur.com"`

2. Rebuilder l'application avec `npm run build`

3. Le fichier `server-config.json` est inclus dans le build, donc l'URL sera celle configurée au moment du build

## Modifications automatiques

Toutes les modifications que vous faites sur le serveur backend se refléteront automatiquement dans l'application desktop car:

- L'application charge le contenu directement depuis le serveur
- Il n'y a pas de cache local des pages
- Chaque fois que l'utilisateur navigue, le contenu est chargé depuis le serveur

**Vous n'avez PAS besoin de redistribuer le .exe quand vous modifiez:**
- Les fichiers HTML/CSS/JS sur le serveur
- Le backend Python
- La base de données

**Vous devez redistribuer le .exe seulement si vous changez:**
- L'URL du serveur (dans `server-config.json`)
- L'icône de l'application
- Les paramètres de l'application Electron elle-même

## Structure

```
desktop-app/
├── main.js              # Point d'entrée Electron
├── package.json         # Configuration npm et build
├── server-config.json   # Configuration de l'URL du serveur
├── icon.ico            # Icône de l'application (à ajouter)
└── dist/               # Dossier de sortie du build (créé automatiquement)
```

## Notes

- L'application se connecte automatiquement au serveur au démarrage
- Si le serveur n'est pas accessible, un message d'erreur s'affiche
- La barre de menu est masquée pour une expérience plus propre
- L'application garde la session de l'utilisateur grâce aux cookies
