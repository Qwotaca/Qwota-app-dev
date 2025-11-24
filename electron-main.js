const { app, BrowserWindow, Menu, shell, dialog, ipcMain } = require('electron');
const path = require('path');

// ============================================
// CONFIGURATION
// ============================================

// URL de production (Render)
const PRODUCTION_URL = 'https://qwota-app-dev.onrender.com';

// URL de développement - LOCALHOST pour tests locaux
const DEVELOPMENT_URL = 'http://localhost:8080';

// Mode: 'production' ou 'development'
const MODE = 'production'; // Mode PRODUCTION pour l'application en ligne

// URL de base du serveur
const BASE_URL = MODE === 'production' ? PRODUCTION_URL : DEVELOPMENT_URL;

// L'app desktop charge directement la page de login (pas la page d'accueil du site web)
const SERVER_URL = `${BASE_URL}/login`;

// ============================================
// VARIABLES GLOBALES
// ============================================

let mainWindow = null;
let isServerReachable = false;

// ============================================
// CRÉATION DE LA FENÊTRE PRINCIPALE
// ============================================

function createWindow() {
  const preloadPath = path.join(__dirname, 'preload.js');
  console.log('[DEBUG] Chemin preload script:', preloadPath);

  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    backgroundColor: '#1e293b',
    icon: path.join(__dirname, 'build/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      sandbox: false,
      preload: preloadPath,
      webviewTag: false,
      devTools: true // Permettre F12
    },
    show: false,
    frame: true,
    titleBarStyle: 'default',
    autoHideMenuBar: true, // Cache la barre de menu (F12 fonctionne toujours)
    fullscreen: false,
    kiosk: false,
    resizable: false, // Empêche le redimensionnement
    maximizable: false, // Empêche la maximisation
    minimizable: true // Permet de minimiser
  });

  // Afficher la fenêtre quand elle est prête
  mainWindow.once('ready-to-show', () => {
    mainWindow.maximize(); // Maximiser la fenêtre
    mainWindow.show();
    console.log('[OK] Fenêtre affichée en plein écran');
  });

  // Supprimer complètement le menu (pas de barre de menu)
  mainWindow.setMenuBarVisibility(false);

  // Empêcher le déplacement de la fenêtre
  mainWindow.setMovable(false);

  // Charger l'application
  loadApplication();

  // Gestion des liens externes (ouvrir dans le navigateur par défaut)
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  // Logs de navigation
  mainWindow.webContents.on('did-start-loading', () => {
    console.log('🔄 Chargement de la page...');
  });

  mainWindow.webContents.on('did-finish-load', () => {
    console.log('[OK] Page chargée avec succès');

    // Debug: Vérifier si electronAPI est disponible dans la page
    mainWindow.webContents.executeJavaScript(`
      console.log('[DEBUG] [DEBUG] window.electronAPI:', typeof window.electronAPI);
      console.log('[DEBUG] [DEBUG] electronAPI.openOAuthPopup:', typeof window.electronAPI?.openOAuthPopup);
      typeof window.electronAPI !== 'undefined' ? 'available' : 'undefined';
    `).then(result => {
      console.log('[DEBUG] [MAIN PROCESS] electronAPI status:', result);
    }).catch(err => {
      console.error('[ERROR] [MAIN PROCESS] Error checking electronAPI:', err);
    });
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('[ERROR] Erreur de chargement:', errorDescription);
    showErrorPage(errorDescription);
  });

  // Débogage en développement
  if (MODE === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// ============================================
// CHARGEMENT DE L'APPLICATION
// ============================================

async function loadApplication() {
  console.log(`[LAUNCH] Connexion à ${SERVER_URL}...`);

  try {
    // Vérifier si le serveur est accessible
    isServerReachable = await checkServerConnection();

    if (isServerReachable) {
      console.log('[OK] Serveur accessible, chargement de l\'application...');
      mainWindow.loadURL(SERVER_URL);
    } else {
      console.error('[ERROR] Serveur non accessible');
      showErrorPage('Impossible de se connecter au serveur');
    }
  } catch (error) {
    console.error('[ERROR] Erreur lors du chargement:', error);
    showErrorPage(error.message);
  }
}

// ============================================
// VÉRIFICATION DE LA CONNEXION AU SERVEUR
// ============================================

async function checkServerConnection() {
  try {
    const { net } = require('electron');

    return new Promise((resolve) => {
      const request = net.request({
        method: 'GET',
        url: SERVER_URL,
        timeout: 10000 // 10 secondes
      });

      request.on('response', (response) => {
        console.log('[OK] Serveur répond avec status:', response.statusCode);
        resolve(response.statusCode === 200 || response.statusCode === 302);
      });

      request.on('error', (error) => {
        console.error('[ERROR] Erreur de connexion:', error.message);
        resolve(false);
      });

      request.on('timeout', () => {
        console.error('[ERROR] Timeout de connexion');
        request.abort();
        resolve(false);
      });

      request.end();
    });
  } catch (error) {
    console.error('[ERROR] Erreur vérification serveur:', error);
    return false;
  }
}

// ============================================
// PAGE D'ERREUR
// ============================================

function showErrorPage(errorMessage) {
  const errorHTML = `
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Erreur de connexion - Qwota</title>
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
          color: #f1f5f9;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          padding: 20px;
        }
        .error-container {
          background: rgba(30, 41, 59, 0.8);
          border: 2px solid #334155;
          border-radius: 16px;
          padding: 48px;
          max-width: 600px;
          text-align: center;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
        }
        .error-icon {
          font-size: 64px;
          margin-bottom: 24px;
        }
        h1 {
          font-size: 28px;
          margin-bottom: 16px;
          color: #f1f5f9;
        }
        p {
          font-size: 16px;
          line-height: 1.6;
          color: #94a3b8;
          margin-bottom: 12px;
        }
        .error-details {
          background: rgba(15, 23, 42, 0.6);
          border: 1px solid #475569;
          border-radius: 8px;
          padding: 16px;
          margin: 24px 0;
          font-family: 'Courier New', monospace;
          font-size: 14px;
          color: #ef4444;
          text-align: left;
        }
        .btn {
          background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
          color: white;
          border: none;
          padding: 12px 32px;
          border-radius: 8px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          margin: 8px;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
        }
        .btn-secondary {
          background: linear-gradient(135deg, #64748b 0%, #475569 100%);
        }
        .server-info {
          margin-top: 24px;
          padding: 16px;
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 8px;
        }
        .server-url {
          color: #60a5fa;
          font-weight: 600;
          word-break: break-all;
        }
      </style>
    </head>
    <body>
      <div class="error-container">
        <div class="error-icon">[WARN]</div>
        <h1>Impossible de se connecter</h1>
        <p>L'application ne peut pas se connecter au serveur Qwota.</p>

        <div class="error-details">
          ${errorMessage}
        </div>

        <div class="server-info">
          <p style="margin-bottom: 8px; color: #94a3b8;">Tentative de connexion à:</p>
          <p class="server-url">${SERVER_URL}</p>
        </div>

        <p style="margin-top: 24px;">Veuillez vérifier:</p>
        <p>• Votre connexion internet</p>
        <p>• Que le serveur Qwota est en ligne</p>

        <div style="margin-top: 32px;">
          <button class="btn" onclick="location.reload()">🔄 Réessayer</button>
          <button class="btn btn-secondary" onclick="window.close()">Quitter</button>
        </div>
      </div>
    </body>
    </html>
  `;

  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHTML)}`);
}

// ============================================
// MENU DE L'APPLICATION
// ============================================

function createMenu() {
  const template = [
    {
      label: 'Fichier',
      submenu: [
        {
          label: 'Actualiser',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            if (mainWindow) {
              loadApplication();
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Quitter',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Édition',
      submenu: [
        { label: 'Annuler', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
        { label: 'Rétablir', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
        { type: 'separator' },
        { label: 'Couper', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: 'Copier', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: 'Coller', accelerator: 'CmdOrCtrl+V', role: 'paste' },
        { label: 'Sélectionner tout', accelerator: 'CmdOrCtrl+A', role: 'selectAll' }
      ]
    },
    {
      label: 'Affichage',
      submenu: [
        { label: 'Plein écran', role: 'togglefullscreen' },
        { type: 'separator' },
        { label: 'Zoom +', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
        { label: 'Zoom -', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
        { label: 'Zoom normal', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' }
      ]
    },
    {
      label: 'Aide',
      submenu: [
        {
          label: 'À propos de Qwota',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'À propos de Qwota',
              message: 'Qwota',
              detail: `Version: 1.0.0\nApplication de gestion pour entrepreneurs\n\nServeur: ${SERVER_URL}`,
              buttons: ['OK']
            });
          }
        },
        { type: 'separator' },
        {
          label: 'Ouvrir dans le navigateur',
          click: () => {
            shell.openExternal(SERVER_URL);
          }
        }
      ]
    }
  ];

  // Ajouter le menu développeur en mode dev
  if (MODE === 'development') {
    template.push({
      label: 'Développeur',
      submenu: [
        { label: 'Outils de développement', role: 'toggleDevTools' },
        { type: 'separator' },
        { label: 'Recharger', role: 'reload' }
      ]
    });
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// ============================================
// POPUP OAUTH (Google, Calendar, etc.)
// ============================================

/**
 * Ouvre une fenêtre popup pour l'authentification OAuth
 * La popup se ferme automatiquement après la redirection
 */
function createOAuthPopup(url) {
  return new Promise((resolve, reject) => {
    const popup = new BrowserWindow({
      width: 600,
      height: 700,
      parent: mainWindow,
      modal: true,
      show: false,
      backgroundColor: '#ffffff',
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true
      }
    });

    // Afficher la popup quand elle est prête
    popup.once('ready-to-show', () => {
      popup.show();
      console.log('🔐 Popup OAuth ouverte');
    });

    // Surveiller les changements d'URL pour détecter la redirection
    popup.webContents.on('did-navigate', (event, navigationUrl) => {
      handleOAuthCallback(navigationUrl, popup, resolve, reject);
    });

    popup.webContents.on('will-redirect', (event, navigationUrl) => {
      handleOAuthCallback(navigationUrl, popup, resolve, reject);
    });

    // Gérer la fermeture de la popup
    popup.on('closed', () => {
      reject(new Error('Popup OAuth fermée par l\'utilisateur'));
    });

    // Charger l'URL OAuth
    popup.loadURL(url);
  });
}

/**
 * Gère la redirection OAuth et ferme la popup
 */
function handleOAuthCallback(url, popup, resolve, reject) {
  // Vérifier si c'est une URL de callback
  if (url.includes('/callback-google') || url.includes('/callback-agenda') || url.includes('/oauth2callback') || url.includes('/gmail/callback') || url.includes('/dashboard')) {
    console.log('[OK] Callback OAuth détecté:', url);

    // Fermer la popup
    if (popup && !popup.isDestroyed()) {
      popup.close();
    }

    // Retourner l'URL de callback
    resolve(url);
  }
}

// Handler IPC pour ouvrir la popup OAuth depuis le renderer
ipcMain.handle('open-oauth-popup', async (event, url) => {
  try {
    console.log('🔐 Ouverture popup OAuth:', url);
    const callbackUrl = await createOAuthPopup(url);
    return { success: true, url: callbackUrl };
  } catch (error) {
    console.error('[ERROR] Erreur popup OAuth:', error);
    return { success: false, error: error.message };
  }
});

// ============================================
// GESTION DE L'APPLICATION
// ============================================

app.whenReady().then(() => {
  console.log('[LAUNCH] Application Electron démarrée');
  console.log(`📍 Mode: ${MODE}`);
  console.log(`🌐 URL cible: ${SERVER_URL}`);

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  console.log('👋 Fermeture de l\'application');
});

// Gestion des erreurs non capturées
process.on('uncaughtException', (error) => {
  console.error('[ERROR] Erreur non capturée:', error);
});

console.log('[OK] Configuration Electron chargée');
