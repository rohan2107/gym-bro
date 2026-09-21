// Bump CACHE_NAME whenever the caching strategy changes: activation deletes every cache with a
// different name, which is how devices drop a shell cached by an older strategy. (v2 served the
// page cache-first for a day, so a device could run the old frontend against the new API.)
const CACHE_NAME = 'gymbro-v3';
const API_CACHE_NAME = 'gymbro-api-v2';
const CACHE_EXPIRATION_TIME = 24 * 60 * 60 * 1000; // 24 hours, for non-hashed static files

// How long a navigation waits for the network before falling back to the cached page. Without
// a limit, network-first hangs on a poor connection instead of opening the app.
const NAVIGATION_TIMEOUT_MS = 4000;

// The page itself. Every route serves the same single-page shell.
const SHELL_URL = '/index.html';

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

const OFFLINE_PAGE =
  '<!DOCTYPE html><html><head><title>Offline</title><style>body{font-family:sans-serif;text-align:center;padding:50px;}h1{color:#ef4444;}</style></head><body><h1>You\'re offline</h1><p>Please check your internet connection.</p><p>Try visiting the app while online first to cache the content.</p></body></html>';

function offlineResponse() {
  return new Response(OFFLINE_PAGE, { headers: { 'Content-Type': 'text/html' } });
}

function isNavigation(request) {
  return (
    request.mode === 'navigate' ||
    (request.headers.get('accept') || '').includes('text/html')
  );
}

// Vite content-hashes everything under /assets/, so a URL never changes meaning and a cached
// copy can never be stale.
function isHashedAsset(url) {
  return url.pathname.startsWith('/assets/');
}

// The page: network first, so a deploy shows up on the next load, falling back to the cached
// shell when offline or when the network is too slow. A late network response still refreshes
// the cache for next time.
function networkFirstPage(request) {
  return new Promise((resolve) => {
    let settled = false;
    const finish = (response) => {
      if (!settled) {
        settled = true;
        resolve(response);
      }
    };
    const fromCache = () =>
      caches.match(request).then((cached) => cached || caches.match(SHELL_URL));

    const timer = setTimeout(() => {
      fromCache().then((cached) => {
        if (cached) finish(cached);
      });
    }, NAVIGATION_TIMEOUT_MS);

    fetch(request)
      .then((response) => {
        clearTimeout(timer);
        if (response.status === 200) {
          const forRequest = response.clone();
          const forShell = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, forRequest);
            cache.put(SHELL_URL, forShell);
          });
        }
        finish(response);
      })
      .catch(() => {
        clearTimeout(timer);
        fromCache().then((cached) => finish(cached || offlineResponse()));
      });
  });
}

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

  // Skip OAuth/auth endpoints - they must go directly to network without caching
  if (url.pathname.startsWith('/api/auth/')) {
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

  // The page itself: network-first (see networkFirstPage)
  if (isNavigation(request)) {
    event.respondWith(networkFirstPage(request));
    return;
  }

  // Static assets: Cache-first, fall back to network
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // Hashed assets never change, so they never expire
        if (isHashedAsset(url)) {
          return cachedResponse;
        }

        // Other files expire after a day
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
          
          // For other resources, just fail gracefully
          return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
        });
    })
  );
});
