/**
 * PRELOAD SCRIPT - Electron
 * Bridge entre le processus principal et le renderer
 * Expose les APIs de manière sécurisée avec contextIsolation
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose les APIs au renderer de manière sécurisée
contextBridge.exposeInMainWorld('electronAPI', {
  /**
   * Ouvrir une popup OAuth (Google, Calendar, etc.)
   * @param {string} url - URL OAuth à ouvrir
   * @returns {Promise<string>} - URL de callback avec les paramètres
   */
  openOAuthPopup: (url) => {
    return ipcRenderer.invoke('open-oauth-popup', url);
  },

  /**
   * Relancer la connexion au serveur (depuis la page d'erreur)
   */
  retryConnection: () => {
    ipcRenderer.send('retry-connection');
  }
});

console.log('[OK] Preload script chargé');
