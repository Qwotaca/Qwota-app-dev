# Guide de Démarrage Rapide - Qwota Desktop

## Comment créer le fichier .exe à distribuer

### 1. Configurer l'URL du serveur (IMPORTANT!)

Avant de créer le .exe, vous devez configurer l'URL de votre serveur dans le fichier `server-config.json`:

**Pour utilisation locale (test):**
```json
{
  "url": "http://127.0.0.1:8080"
}
```

**Pour distribution aux utilisateurs (production):**
```json
{
  "url": "https://votre-serveur-en-ligne.com"
}
```

⚠️ **ATTENTION:** L'URL configurée dans `server-config.json` sera celle utilisée par le .exe. Assurez-vous qu'elle pointe vers un serveur accessible par vos utilisateurs!

### 2. Créer le fichier .exe

Ouvrez un terminal dans le dossier `desktop-app` et exécutez:

```bash
npm run build
```

Le fichier .exe sera créé dans le dossier `desktop-app/dist/`.

### 3. Distribuer l'application

Deux options:

**Option 1 - Installer l'application (recommandé):**
- Fichier: `desktop-app/dist/Qwota Setup X.X.X.exe`
- Distribuer ce fichier à vos utilisateurs
- Double-cliquer pour installer l'application
- L'application sera ajoutée au menu Démarrer

**Option 2 - Version portable:**
- Créer une version portable avec: `npm run build:dir`
- Dossier: `desktop-app/dist/win-unpacked/`
- Compresser tout le dossier en .zip
- L'utilisateur peut extraire et lancer `Qwota.exe` directement

## Avantages de cette solution

### ✅ Modifications automatiques
Quand vous modifiez votre serveur backend, les changements sont **automatiquement** visibles dans l'application desktop de tous vos utilisateurs!

**Vous n'avez PAS besoin de redistribuer le .exe quand vous:**
- Modifiez les pages HTML/CSS/JS
- Changez le backend Python
- Ajoutez de nouvelles fonctionnalités au serveur
- Corrigez des bugs

L'application desktop charge tout depuis le serveur en temps réel!

### ✅ Quand redistribuer le .exe?

Vous devez recréer et redistribuer le .exe UNIQUEMENT si vous:
- Changez l'URL du serveur
- Modifiez l'icône de l'application
- Changez les paramètres Electron (taille de fenêtre, etc.)

## Prérequis pour vos utilisateurs

Vos utilisateurs ont besoin de:
1. Windows (x64)
2. Connexion internet (pour accéder au serveur)
3. C'est tout! L'application est autonome.

## Tester avant de distribuer

Avant de distribuer le .exe à vos utilisateurs:

1. **Démarrez votre serveur backend:**
   ```bash
   cd C:\Users\zachl\OneDrive\Bureau\qwota-app-main
   python -m uvicorn main:app --reload --host 127.0.0.1 --port 8080
   ```

2. **Testez en local:**
   - Utilisez `server-config.json` avec `"url": "http://127.0.0.1:8080"`
   - Créez le .exe avec `npm run build`
   - Installez et testez le .exe

3. **Testez en production:**
   - Déployez votre serveur sur un hébergeur (Heroku, AWS, etc.)
   - Changez `server-config.json` avec l'URL publique
   - Recréez le .exe avec `npm run build`
   - Testez depuis un autre ordinateur

## Déployer le serveur en ligne

Pour que vos utilisateurs puissent utiliser l'application de n'importe où, vous devez héberger votre serveur backend en ligne.

Quelques options:
- **Heroku** (gratuit pour commencer)
- **Render** (gratuit)
- **PythonAnywhere** (gratuit)
- **AWS/Azure/Google Cloud** (payant mais robuste)

Une fois déployé, changez l'URL dans `server-config.json` et rebuilder le .exe.

## Support et troubleshooting

### L'application affiche "Impossible de se connecter au serveur"
- Vérifiez que le serveur est démarré
- Vérifiez que l'URL dans `server-config.json` est correcte
- Testez l'URL dans un navigateur web d'abord

### L'application ne se lance pas
- Vérifiez que vous utilisez Windows 64-bit
- Essayez de lancer en mode administrateur
- Vérifiez l'antivirus (peut bloquer l'installation)

### Les modifications du serveur ne se reflètent pas
- Forcez un rafraîchissement dans l'application (F5)
- Vérifiez que vous modifiez le bon serveur
- Vérifiez que le serveur est bien redémarré après modifications
