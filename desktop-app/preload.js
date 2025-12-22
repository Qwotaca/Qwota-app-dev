const { contextBridge, ipcRenderer } = require('electron');

// Exposer les fonctions OAuth à la page web
contextBridge.exposeInMainWorld('electronAPI', {
  // Ouvrir le modal OAuth
  openOAuthModal: async (url, type) => {
    return await ipcRenderer.invoke('open-oauth-modal', url, type);
  },

  // Fermer le modal OAuth
  closeOAuthModal: async () => {
    return await ipcRenderer.invoke('close-oauth-modal');
  },

  // Écouter les événements de succès OAuth
  onOAuthSuccess: (callback) => {
    ipcRenderer.on('oauth-success', (event, type) => callback(type));
  }
});
