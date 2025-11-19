const CACHE_NAME = 'qwota-v137';
const urlsToCache = [
  '/',
  // '/frontend/login.html', // JAMAIS CACHER - doit toujours être frais
  '/frontend/dashboard_user.html',
  '/frontend/dashboardcoach.html',
  '/frontend/central.html',
  '/frontend/calcul.html',
  '/frontend/creer_soumission.html',
  '/frontend/facture.html',
  '/frontend/gqp.html',
  '/frontend/travaux.html',
  '/frontend/connect_agenda.html',
  '/frontend/facturationqe.html',
  '/frontend/gestionemployes.html',
  '/frontend/avis.html',
  '/frontend/rpo.html',
  '/frontend/support.html',
  '/static/manifest.webmanifest',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png'
];

// Installation du service worker avec gestion d'erreurs
self.addEventListener('install', (event) => {
  // Force le nouveau service worker a s'activer immediatement
  self.skipWaiting();

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        // Cache chaque fichier individuellement pour eviter qu'un echec bloque tout
        return Promise.all(
          urlsToCache.map((url) => {
            return cache.add(url).catch((err) => {
              console.log('[SW] Impossible de mettre en cache:', url, err);
            });
          })
        );
      })
  );
});

// Activation du service worker
self.addEventListener('activate', (event) => {
  // Prend le controle de toutes les pages immediatement
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Interception des requêtes
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // NE JAMAIS CACHER LES REQUÊTES API, VENTES, LOGIN ET ONBOARDING - toujours aller chercher les données fraîches
  if (url.pathname.startsWith('/api/') ||
      url.pathname.startsWith('/ventes/') ||
      url.pathname.startsWith('/get-') ||
      url.pathname === '/login' ||
      url.pathname === '/onboarding') {
    event.respondWith(fetch(event.request));
    return;
  }

  // Ne mettre en cache que les requêtes GET pour les fichiers statiques
  if (event.request.method !== 'GET') {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Cache hit - return response
        if (response) {
          return response;
        }

        return fetch(event.request).then(
          (response) => {
            // Check if we received a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // IMPORTANT: Clone the response
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });

            return response;
          }
        );
      })
  );
});