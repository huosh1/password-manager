// Service Worker pour PWA Password Manager
const CACHE_NAME = 'password-manager-v1';
const OFFLINE_URL = '/offline';

// Fichiers à mettre en cache pour fonctionnement hors ligne
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/icon-192.png',
  '/static/icon-512.png',
  // Les styles et scripts sont inline, donc pas besoin de les cacher séparément
];

// Installation du Service Worker
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        // Force l'activation immédiate
        return self.skipWaiting();
      })
  );
});

// Activation du Service Worker
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Supprimer les anciens caches
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Prendre contrôle immédiatement
      return self.clients.claim();
    })
  );
});

// Interception des requêtes réseau
self.addEventListener('fetch', (event) => {
  // Ignorer les requêtes non-HTTP
  if (!event.request.url.startsWith('http')) {
    return;
  }
  
  // Stratégie: Network First, puis Cache
  if (event.request.url.includes('/api/')) {
    // Pour les API: Toujours essayer le réseau d'abord
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          return response;
        })
        .catch(() => {
          // Si pas de réseau, retourner une réponse d'erreur
          return new Response(
            JSON.stringify({ 
              success: false, 
              error: 'Offline - please check your connection' 
            }),
            { 
              status: 503,
              statusText: 'Service Unavailable',
              headers: { 'Content-Type': 'application/json' }
            }
          );
        })
    );
  } else {
    // Pour les ressources statiques: Cache First, puis Network
    event.respondWith(
      caches.match(event.request)
        .then((response) => {
          // Retourner depuis le cache si disponible
          if (response) {
            return response;
          }
          
          // Sinon, essayer le réseau
          return fetch(event.request).then((response) => {
            // Ne pas cacher les réponses d'erreur
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            
            // Cloner la réponse car elle peut être utilisée qu'une fois
            const responseToCache = response.clone();
            
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
            
            return response;
          });
        })
        .catch(() => {
          // Si aucune correspondance en cache et pas de réseau
          return caches.match('/');
        })
    );
  }
});

// Gestion des messages du client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Gestion de la synchronisation en arrière-plan
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    console.log('[SW] Background sync triggered');
    event.waitUntil(
      // Ici on pourrait synchroniser les données avec Dropbox
      // quand la connexion revient
      Promise.resolve()
    );
  }
});

// Notifications push (optionnel)
self.addEventListener('push', (event) => {
  if (event.data) {
    const data = event.data.json();
    
    const options = {
      body: data.body || 'Password Manager notification',
      icon: '/static/icon-192.png',
      badge: '/static/icon-96.png',
      vibrate: [200, 100, 200],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: data.primaryKey || 1
      },
      actions: [
        {
          action: 'open',
          title: 'Open Password Manager',
          icon: '/static/icon-96.png'
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/static/icon-96.png'
        }
      ]
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title || 'Password Manager', options)
    );
  }
});

// Gestion des clics sur notifications
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'open') {
    event.waitUntil(
      clients.matchAll().then((clientList) => {
        if (clientList.length > 0) {
          return clientList[0].focus();
        }
        return clients.openWindow('/');
      })
    );
  }
});