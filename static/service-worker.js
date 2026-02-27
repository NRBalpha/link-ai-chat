const CACHE_NAME = 'enku-v1';

const PRECACHE_URLS = [
  '/',
  '/chat',
  '/welcome',
  '/signin',
  '/signup',
  '/icons/icon-192.svg',
  '/icons/icon-512.svg',
  '/manifest.json',
  '/loading_transparent.apng',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

const API_ROUTES = [
  '/chat',
  '/chat/stream',
  '/transcribe',
  '/send-verification',
  '/verify-code',
  '/static/uploads/'
];

function isApiRequest(url) {
  const path = new URL(url).pathname;
  return API_ROUTES.some(route => {
    if (route === '/chat') {
      return path === '/chat' && arguments[1] && arguments[1] !== 'GET';
    }
    return path.startsWith(route);
  });
}

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;

  // Skip non-GET requests (all API calls are POST)
  if (request.method !== 'GET') return;

  // Skip API-like GET routes that return dynamic data
  const path = new URL(request.url).pathname;
  if (path.startsWith('/static/uploads/')) return;

  event.respondWith(
    fetch(request)
      .then(response => {
        // Cache successful responses
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // Serve from cache when offline
        return caches.match(request);
      })
  );
});
