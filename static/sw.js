// Service Worker désactivé
// Ce fichier existe uniquement pour désenregistrer le SW s'il est déjà enregistré

self.addEventListener('install', function(event) {
  console.log('[SW] Installation - auto-destruction en cours...');
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  console.log('[SW] Activation - désenregistrement...');
  event.waitUntil(
    self.registration.unregister().then(function() {
      console.log('[SW] Service Worker désenregistré avec succès');
      return self.clients.matchAll();
    }).then(function(clients) {
      clients.forEach(client => client.navigate(client.url));
    })
  );
});
