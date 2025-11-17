const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
const fs = require('fs');

// Configuration du serveur
const CONFIG_FILE = path.join(__dirname, 'server-config.json');
let serverConfig = {
  url: 'http://127.0.0.1:8080/login'
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
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));

  // Pas de menu pour le splash
  splashWindow.setMenu(null);
}

function createWindow() {
  // Créer la fenêtre du navigateur (cachée au départ)
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
      webSecurity: true
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
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('Erreur de chargement:', errorDescription);

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

  // Intercepter les nouvelles fenêtres pour les ouvrir dans la même fenêtre
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
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
