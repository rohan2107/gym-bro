const CACHE_NAME = 'gymbro-v2';
const API_CACHE_NAME = 'gymbro-api-v2';
const CACHE_EXPIRATION_TIME = 24 * 60 * 60 * 1000; // 24 hours

// Assets to cache on install
// In dev mode, caching is minimal. In production, more assets are cached.
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      // Try to cache static assets, but don't fail install if it fails
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.log('Cache addAll failed:', err);
        // Still install even if initial cache fails
        return Promise.resolve();
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== API_CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - different strategies for API vs static assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension:// and other non-http(s) schemes
  if (!url.protocol.startsWith('http')) {
    return;
  }

  // Skip Vite HMR requests (dev mode hot reload)
  if (url.searchParams.has('t') || url.pathname.includes('/@vite/') || url.pathname.includes('/@fs/')) {
    return;
  }

  // Skip WebSocket connections
  if (url.pathname === '/' && url.searchParams.has('token')) {
    return;
  }

  // API requests: Network-first, fall back to cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Clone response before caching
          const responseClone = response.clone();
          caches.open(API_CACHE_NAME).then((cache) => {
            cache.put(request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // If network fails, try cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Return offline response for API failures
            return new Response(
              JSON.stringify({ error: 'Offline', offline: true }),
              {
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'application/json' },
              }
            );
          });
        })
    );
    return;
  }

  // Static assets: Cache-first, fall back to network
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // Check if cache is expired
        const dateHeader = cachedResponse.headers.get('date');
        const cachedTime = dateHeader ? new Date(dateHeader).getTime() : 0;
        const now = Date.now();
        
        if (now - cachedTime < CACHE_EXPIRATION_TIME) {
          return cachedResponse;
        }
      }

      // Fetch from network and cache for next time
      return fetch(request)
        .then((response) => {
          // Cache successful responses
          if (response.status === 200) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Network failed - try serving from expired cache
          if (cachedResponse) {
            return cachedResponse; // Serve stale cache
          }
          
          // For HTML navigation requests, try to serve index.html from cache
          if (request.mode === 'navigate' || request.headers.get('accept')?.includes('text/html')) {
            return caches.match('/index.html').then((indexResponse) => {
              if (indexResponse) {
                return indexResponse;
              }
              // Last resort: offline page
              return new Response(
                '<!DOCTYPE html><html><head><title>Offline</title><style>body{font-family:sans-serif;text-align:center;padding:50px;}h1{color:#ef4444;}</style></head><body><h1>You\'re offline</h1><p>Please check your internet connection.</p><p>Try visiting the app while online first to cache the content.</p></body></html>',
                { headers: { 'Content-Type': 'text/html' } }
              );
            });
          }
          
          // For other resources, just fail gracefully
          return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
        });
    })
  );
});
