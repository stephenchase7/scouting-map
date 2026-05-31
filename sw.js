// NYRB Scouting Service Worker
const CACHE_NAME = 'nyrb-scouting-v1';
const OFFLINE_URL = '/scouts.html';

// Files to cache for offline use
const STATIC_ASSETS = [
  '/',
  '/scouts.html',
  '/index.html',
  '/team.html',
  '/manifest.json',
  '/MLS Logos/NYRB.png'
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('[SW] Installing service worker...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating service worker...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(name => name !== CACHE_NAME)
          .map(name => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip cross-origin requests (except Supabase which we want to handle)
  if (!url.origin.includes(self.location.origin) &&
      !url.origin.includes('supabase')) {
    return;
  }

  // For Supabase API calls - network first, fail silently
  if (url.origin.includes('supabase')) {
    event.respondWith(
      fetch(request)
        .catch(() => {
          console.log('[SW] Supabase request failed, offline mode');
          return new Response(JSON.stringify({ error: 'offline' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
          });
        })
    );
    return;
  }

  // For HTML pages - network first with cache fallback
  if (request.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Clone and cache successful responses
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, responseClone));
          return response;
        })
        .catch(() => {
          console.log('[SW] Serving cached HTML:', request.url);
          return caches.match(request) || caches.match(OFFLINE_URL);
        })
    );
    return;
  }

  // For other assets - cache first with network fallback
  event.respondWith(
    caches.match(request)
      .then(cachedResponse => {
        if (cachedResponse) {
          // Return cached version, but update cache in background
          fetch(request).then(response => {
            caches.open(CACHE_NAME).then(cache => cache.put(request, response));
          }).catch(() => {});
          return cachedResponse;
        }

        // Not in cache, fetch from network
        return fetch(request)
          .then(response => {
            // Cache successful responses
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, responseClone));
            return response;
          });
      })
  );
});

// Handle messages from the main page
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Background sync for offline actions
self.addEventListener('sync', event => {
  if (event.tag === 'sync-observations') {
    console.log('[SW] Background sync triggered');
    event.waitUntil(syncPendingData());
  }
});

async function syncPendingData() {
  // This would sync pending observations when back online
  // The actual sync logic is in scouts.html
  const clients = await self.clients.matchAll();
  clients.forEach(client => {
    client.postMessage({ type: 'SYNC_COMPLETE' });
  });
}
