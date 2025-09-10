// ePetCare Vet Portal Service Worker

const CACHE_NAME = 'epetcare-vet-portal-v1';
const OFFLINE_URL = '/vet-portal/offline/';
const OFFLINE_IMG = '/static/vet_portal/img/offline.svg';

// Assets to cache immediately
const PRECACHE_URLS = [
  '/vet-portal/',
  '/vet-portal/login/',
  '/vet-portal/offline/',
  '/static/vet_portal/css/styles.css',
  '/static/vet_portal/js/app.js',
  '/static/vet_portal/img/icon-192x192.png',
  '/static/vet_portal/img/icon-512x512.png',
  '/static/vet_portal/img/offline.svg',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js'
];

// URLs that should be cached when visited
const DYNAMIC_CACHE_URLS = [
  '/vet-portal/patients/',
  '/vet-portal/appointments/'
];

// Install event - precache important resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('Pre-caching resources');
      return cache.addAll(PRECACHE_URLS);
    })
  );
  
  // Activate the new service worker immediately
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          return cacheName.startsWith('epetcare-vet-portal-') && cacheName !== CACHE_NAME;
        }).map(cacheName => {
          console.log('Deleting old cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    })
  );
  
  // Claim clients so the service worker is in control immediately
  event.waitUntil(self.clients.claim());
});

// Fetch event - network-first strategy with fallback to cache
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // Skip non-GET requests and browser extensions
  if (event.request.method !== 'GET' || url.protocol === 'chrome-extension:') {
    return;
  }
  
  // Handle API requests - network only with offline error handling
  if (url.pathname.startsWith('/vet-portal/api/')) {
    event.respondWith(
      fetch(event.request)
        .catch(error => {
          console.log('API request failed, network error:', error);
          
          // If it's a GET request, we might have it cached
          if (event.request.method === 'GET') {
            return caches.match(event.request).then(cachedResponse => {
              if (cachedResponse) {
                // Add an X-Offline header to indicate this is cached data
                const headers = new Headers(cachedResponse.headers);
                headers.append('X-Offline', 'true');
                
                return new Response(cachedResponse.body, {
                  status: cachedResponse.status,
                  statusText: cachedResponse.statusText + ' (Offline)',
                  headers: headers
                });
              }
              
              // Return a JSON error for API requests
              return new Response(JSON.stringify({
                error: 'You are offline. Changes will be synced when you reconnect.'
              }), {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
              });
            });
          }
          
          // For non-GET API requests, store them for later sync
          return storeRequestForSync(event.request.clone())
            .then(() => {
              return new Response(JSON.stringify({
                message: 'Your changes have been saved and will be synced when you reconnect.'
              }), {
                status: 202,
                headers: { 'Content-Type': 'application/json' }
              });
            });
        })
    );
    return;
  }
  
  // For HTML pages - network first, then cache, then offline page
  if (event.request.headers.get('Accept').includes('text/html')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache the successful response
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
          return response;
        })
        .catch(() => {
          // Try to get from cache first
          return caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // If not in cache, return the offline page
            return caches.match(OFFLINE_URL);
          });
        })
    );
    return;
  }
  
  // For other assets - cache first, then network
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      
      // Not in cache, get from network
      return fetch(event.request).then(response => {
        // Check if we should cache this URL
        const shouldCache = DYNAMIC_CACHE_URLS.some(url => 
          event.request.url.includes(url)
        ) || event.request.url.includes('/static/');
        
        if (shouldCache) {
          const responseClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseClone);
          });
        }
        
        return response;
      }).catch(() => {
        // For image requests, return a default offline image
        if (event.request.headers.get('Accept').includes('image/')) {
          return caches.match(OFFLINE_IMG);
        }
      });
    })
  );
});

// Background sync for offline changes
self.addEventListener('sync', event => {
  if (event.tag === 'sync-offline-changes') {
    event.waitUntil(syncOfflineChanges());
  }
});

// Store offline requests for later sync
async function storeRequestForSync(request) {
  try {
    const db = await openIndexedDB();
    const tx = db.transaction('offline-requests', 'readwrite');
    const store = tx.objectStore('offline-requests');
    
    const requestData = {
      url: request.url,
      method: request.method,
      headers: Array.from(request.headers.entries()),
      timestamp: Date.now()
    };
    
    // If it has a body, clone and store it
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      requestData.body = await request.clone().text();
    }
    
    await store.add(requestData);
    await tx.complete;
    
    // Register for background sync if supported
    if ('sync' in self.registration) {
      await self.registration.sync.register('sync-offline-changes');
    }
    
    return true;
  } catch (error) {
    console.error('Failed to store request for offline sync:', error);
    return false;
  }
}

// Sync offline changes when back online
async function syncOfflineChanges() {
  try {
    const db = await openIndexedDB();
    const tx = db.transaction('offline-requests', 'readwrite');
    const store = tx.objectStore('offline-requests');
    const requests = await store.getAll();
    
    // Process each stored request
    const syncPromises = requests.map(async (requestData) => {
      try {
        const request = new Request(requestData.url, {
          method: requestData.method,
          headers: new Headers(requestData.headers),
          body: requestData.body
        });
        
        // Attempt to send the request
        const response = await fetch(request);
        
        if (response.ok) {
          // If successful, delete from store
          await store.delete(requestData.id);
          console.log('Successfully synced offline request:', requestData.url);
          return { success: true, url: requestData.url };
        } else {
          console.error('Failed to sync request:', response.statusText);
          return { success: false, url: requestData.url, error: response.statusText };
        }
      } catch (error) {
        console.error('Error syncing request:', error);
        return { success: false, url: requestData.url, error: error.message };
      }
    });
    
    const results = await Promise.all(syncPromises);
    await tx.complete;
    
    // Notify the client about sync results
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'sync-complete',
        results: results
      });
    });
    
    return results;
  } catch (error) {
    console.error('Failed to sync offline changes:', error);
    return [];
  }
}

// Helper function to open IndexedDB
function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('epetcare-vet-portal-db', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('offline-requests')) {
        db.createObjectStore('offline-requests', { 
          keyPath: 'id',
          autoIncrement: true 
        });
      }
    };
  });
}
