const { app, BrowserWindow, Menu, ipcMain, BrowserView } = require('electron');
const path = require('path');
const fs = require('fs');

// Configuration du serveur
const CONFIG_FILE = path.join(__dirname, 'server-config.json');
let serverConfig = {
  url: 'http://localhost:8080/login'
};

// Charger la configuration si elle existe
if (fs.existsSync(CONFIG_FILE)) {
  try {
    serverConfig = JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
  } catch (error) {
    console.error('Erreur lors du chargement de la configuration:', error);
  }
} else {
  // Créer le fichier de configuration par défaut
  fs.writeFileSync(CONFIG_FILE, JSON.stringify(serverConfig, null, 2));
}

let mainWindow;
let splashWindow;
let oauthView;
let pageCache = {}; // Cache pour les pages préchargées

// Fonction pour précharger toutes les pages principales en arrière-plan
function preloadAllPages() {
  // Vérifier que mainWindow existe et n'est pas détruite
  if (!mainWindow || mainWindow.isDestroyed()) {
    console.log('[ELECTRON] ⚠️  Impossible de précharger: mainWindow non disponible');
    return;
  }

  const baseUrl = serverConfig.url.replace('/login', '');

  const pagesToPreload = [
    '/dashboard',
    '/calcul',
    '/soumissions',
    '/gqp',
    '/travaux',
    '/facture',
    '/rpo',
    '/centralevue',
    '/gamification',
    '/gestionemployes',
    '/facturationqe',
    '/avis',
    '/centrale',
    '/ventes'
  ];

  console.log(`[ELECTRON] 📋 Préchargement de ${pagesToPreload.length} pages en arrière-plan...`);

  let loadedCount = 0;
  const totalPages = pagesToPreload.length;

  // Envoyer la progression initiale au splash
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('loading-progress', { loaded: 0, total: totalPages });
  }

  pagesToPreload.forEach((pagePath, index) => {
    // Vérifier à nouveau que mainWindow existe avant chaque création de view
    if (!mainWindow || mainWindow.isDestroyed()) {
      console.log('[ELECTRON] ⚠️  Arrêt du préchargement: mainWindow fermée');
      return;
    }

    const view = new BrowserView({
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        webSecurity: true,
        session: mainWindow.webContents.session // Partager la même session pour le cache
      }
    });

    // Positionner hors écran (invisible mais chargé)
    view.setBounds({ x: 0, y: 0, width: 1, height: 1 });

    // Ajouter à la fenêtre (mais invisible)
    mainWindow.addBrowserView(view);

    // Charger la page
    const fullUrl = baseUrl + pagePath;
    view.webContents.loadURL(fullUrl);

    // Quand la page est chargée
    view.webContents.on('did-finish-load', () => {
      loadedCount++;
      console.log(`[ELECTRON] ✅ Page préchargée (${loadedCount}/${totalPages}): ${pagePath}`);

      // Envoyer la progression au splash
      if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.send('loading-progress', { loaded: loadedCount, total: totalPages });
      }

      // Quand toutes les pages sont chargées
      if (loadedCount === totalPages) {
        console.log('[ELECTRON] 🎉 TOUTES LES PAGES SONT PRÉCHARGÉES!');

        // Envoyer l'événement de fin au splash
        if (splashWindow && !splashWindow.isDestroyed()) {
          splashWindow.webContents.send('loading-complete');
        }

        // Fermer le splash et montrer la fenêtre principale
        setTimeout(() => {
          if (splashWindow && !splashWindow.isDestroyed()) {
            splashWindow.close();
          }
          mainWindow.show();

          // Les retirer de l'affichage mais les garder en cache
          const views = mainWindow.getBrowserViews();
          views.forEach(v => {
            if (v !== oauthView) { // Ne pas toucher à l'OAuth view
              mainWindow.removeBrowserView(v);
            }
          });
          console.log('[ELECTRON] 🗑️ BrowserViews temporaires retirées (cache conservé)');
        }, 1000);
      }
    });

    // Stocker dans le cache
    pageCache[pagePath] = view;
  });
}

function createSplashScreen() {
  // Créer la fenêtre splash (popup stylé)
  splashWindow = new BrowserWindow({
    width: 900,
    height: 650,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    center: true,
    resizable: false,
    movable: false,
    skipTaskbar: true,
    webPreferences: {
      nodeIntegration: true, // Permettre require('electron') dans le splash
      contextIsolation: false // Désactiver l'isolation pour le splash (il ne charge pas de contenu externe)
    }
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));

  // Pas de menu pour le splash
  splashWindow.setMenu(null);
}

function createWindow() {
  // Créer la fenêtre du navigateur
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    resizable: false,
    movable: false,
    minimizable: true,
    maximizable: false,
    closable: true,
    show: false, // Ne pas montrer tout de suite
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      webSecurity: true,
      preload: path.join(__dirname, 'preload.js'),
      cache: true // Activer le cache HTTP
    },
    icon: path.join(__dirname, 'icon.ico'),
    title: 'Qwota',
    backgroundColor: '#0f172a'
  });

  // Masquer la barre de menu
  Menu.setApplicationMenu(null);

  // Maximiser la fenêtre au démarrage (mais garder la barre de titre)
  mainWindow.maximize();

  // Ajouter des raccourcis clavier pour refresh et DevTools
  mainWindow.webContents.on('before-input-event', (event, input) => {
    // F5 ou Ctrl+R : Refresh normal
    if (input.key === 'F5' || (input.control && input.key === 'r')) {
      event.preventDefault();
      mainWindow.webContents.reload();
    }

    // Ctrl+Shift+R ou Ctrl+F5 : Hard refresh (vide le cache)
    if ((input.control && input.shift && input.key === 'R') || (input.control && input.key === 'F5')) {
      event.preventDefault();
      mainWindow.webContents.session.clearCache().then(() => {
        mainWindow.webContents.reload();
      });
    }

    // F12 : Toggle DevTools (pour debug)
    if (input.key === 'F12') {
      event.preventDefault();
      mainWindow.webContents.toggleDevTools();
    }
  });

  // Charger l'URL du serveur
  mainWindow.loadURL(serverConfig.url);

  // Quand la page est chargée, afficher la fenêtre
  mainWindow.webContents.on('did-finish-load', () => {
    mainWindow.show();
  });

  // Ouvrir les DevTools en mode développement (optionnel)
  // mainWindow.webContents.openDevTools();

  // Gérer la fermeture de la fenêtre
  mainWindow.on('closed', function () {
    mainWindow = null;
  });

  // Gérer les erreurs de chargement
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error('=== ERREUR DE CHARGEMENT ===');
    console.error('URL:', validatedURL);
    console.error('Code d\'erreur:', errorCode);
    console.error('Description:', errorDescription);
    console.error('==========================');

    // Fermer le splash en cas d'erreur
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }

    // Afficher la fenêtre principale avec le message d'erreur
    mainWindow.show();

    mainWindow.loadURL(`data:text/html;charset=utf-8,
      <!DOCTYPE html>
      <html>
        <head>
          <title>Erreur de connexion</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              background: #0f172a;
              color: white;
              display: flex;
              justify-content: center;
              align-items: center;
              height: 100vh;
              margin: 0;
              text-align: center;
            }
            .error-container {
              padding: 40px;
              max-width: 600px;
            }
            h1 {
              color: #ef4444;
              margin-bottom: 20px;
            }
            p {
              margin: 10px 0;
              line-height: 1.6;
            }
            .server-url {
              background: rgba(255, 255, 255, 0.1);
              padding: 10px;
              border-radius: 5px;
              margin: 20px 0;
              font-family: monospace;
            }
            .error-details {
              background: rgba(239, 68, 68, 0.1);
              padding: 15px;
              border-radius: 5px;
              margin: 20px 0;
              font-family: monospace;
              font-size: 0.9em;
            }
            .instructions {
              margin-top: 30px;
              padding: 20px;
              background: rgba(59, 130, 246, 0.1);
              border-radius: 8px;
              text-align: left;
            }
            .instructions ol {
              margin: 10px 0;
              padding-left: 20px;
            }
            .instructions li {
              margin: 10px 0;
            }
          </style>
        </head>
        <body>
          <div class="error-container">
            <h1>[WARN] Impossible de se connecter au serveur</h1>
            <p>L'application ne peut pas se connecter au serveur Qwota.</p>
            <div class="server-url">
              URL du serveur: ${serverConfig.url}
            </div>
            <div class="error-details">
              <strong>Détails de l'erreur:</strong><br>
              Code: ${errorCode}<br>
              Description: ${errorDescription}
            </div>
            <div class="instructions">
              <h3>Pour résoudre ce problème:</h3>
              <ol>
                <li>Assurez-vous que le serveur Qwota est démarré</li>
                <li>Vérifiez que l'URL du serveur est correcte dans le fichier:<br>
                    <code>server-config.json</code></li>
                <li>Redémarrez l'application après avoir démarré le serveur</li>
              </ol>
            </div>
          </div>
        </body>
      </html>
    `);
  });

  // Permettre les popups OAuth, bloquer les autres
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    // Autoriser les popups OAuth Google
    if (url.includes('accounts.google.com') || url.includes('oauth')) {
      return { action: 'allow' };
    }
    // Autres URLs: charger dans la fenêtre principale
    mainWindow.loadURL(url);
    return { action: 'deny' };
  });
}

// Cette méthode sera appelée quand Electron aura fini de s'initialiser
app.whenReady().then(() => {
  // Créer la fenêtre principale directement
  createWindow();

  app.on('activate', function () {
    // Sur macOS, il est courant de recréer une fenêtre quand
    // l'icône du dock est cliquée et qu'il n'y a pas d'autres fenêtres ouvertes.
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quitter quand toutes les fenêtres sont fermées, sauf sur macOS
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// Gestion de l'OAuth Google avec BrowserView
ipcMain.handle('open-oauth-modal', async (event, url, type) => {
  if (!mainWindow) return { success: false, error: 'No main window' };

  // Créer la BrowserView pour OAuth
  oauthView = new BrowserView({
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: true
    }
  });

  // Ajouter la vue à la fenêtre principale
  mainWindow.addBrowserView(oauthView);

  // Positionner la BrowserView (modal-like, centrée)
  const { width, height } = mainWindow.getBounds();
  const viewWidth = 800;
  const viewHeight = 700;
  const x = Math.floor((width - viewWidth) / 2);
  const y = Math.floor((height - viewHeight) / 2);

  oauthView.setBounds({
    x: x,
    y: y,
    width: viewWidth,
    height: viewHeight
  });

  // Charger l'URL OAuth
  oauthView.webContents.loadURL(url);

  // Écouter l'événement de navigation
  let callbackDetected = false;

  const closeOAuthView = () => {
    if (callbackDetected) return;
    callbackDetected = true;

    console.log('✅ OAuth callback - fermeture BrowserView');

    setTimeout(() => {
      if (oauthView) {
        mainWindow.removeBrowserView(oauthView);
        oauthView.webContents.destroy();
        oauthView = null;
        console.log('✅ BrowserView détruite');
      }

      // Notifier la page principale
      mainWindow.webContents.send('oauth-success', type);
      console.log('✅ Message oauth-success envoyé:', type);
    }, 1500);
  };

  // Détecter quand une page est chargée
  oauthView.webContents.on('did-finish-load', () => {
    if (!oauthView) return;

    try {
      const url = oauthView.webContents.getURL();
      console.log('📄 Page chargée:', url);

      // Vérifier si c'est le callback
      if (url.includes('/gmail/callback') || url.includes('/oauth2callback')) {
        console.log('🎯 Callback détecté!');
        closeOAuthView();
        return; // Ne pas injecter le bouton si on ferme
      }

      // Injecter un bouton de fermeture sur toutes les autres pages
      oauthView.webContents.executeJavaScript(`
        if (!document.getElementById('oauth-close-btn')) {
          const closeBtn = document.createElement('div');
          closeBtn.id = 'oauth-close-btn';
          closeBtn.innerHTML = '✕';
          closeBtn.style.cssText = 'position: fixed; top: 10px; right: 10px; z-index: 999999; background: #ef4444; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 20px; font-weight: bold; box-shadow: 0 2px 8px rgba(0,0,0,0.3);';
          closeBtn.onclick = () => {
            console.log('❌ Bouton fermeture cliqué');
          };
          document.body.appendChild(closeBtn);
        }
      `).catch(err => console.error('Erreur injection bouton:', err));
    } catch(err) {
      console.error('❌ Erreur did-finish-load:', err);
    }
  });

  return { success: true };
});

// Fermer l'OAuth modal
ipcMain.handle('close-oauth-modal', async () => {
  if (oauthView) {
    mainWindow.removeBrowserView(oauthView);
    oauthView.webContents.destroy();
    oauthView = null;
  }
  return { success: true };
});
