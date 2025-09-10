// ePetCare Vet Portal Main JavaScript

// Check if the browser is online or offline
function updateOnlineStatus() {
    const offlineIndicator = document.getElementById('offline-indicator');
    
    if (!navigator.onLine && offlineIndicator) {
        offlineIndicator.classList.add('show');
    } else if (offlineIndicator) {
        offlineIndicator.classList.remove('show');
    }
}

// Listen for online/offline events
window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Create offline indicator if it doesn't exist
    if (!document.getElementById('offline-indicator')) {
        const offlineIndicator = document.createElement('div');
        offlineIndicator.id = 'offline-indicator';
        offlineIndicator.className = 'offline-indicator';
        offlineIndicator.innerHTML = '<i class="bi bi-wifi-off me-2"></i> You are offline';
        document.body.appendChild(offlineIndicator);
    }
    
    // Check initial online status
    updateOnlineStatus();
    
    // Initialize toast notifications
    const toastElements = document.querySelectorAll('.toast');
    if (toastElements.length > 0) {
        toastElements.forEach(toast => {
            const bsToast = new bootstrap.Toast(toast, {
                autohide: true,
                delay: 5000
            });
            bsToast.show();
        });
    }
    
    // Listen for service worker messages
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.addEventListener('message', event => {
            if (event.data && event.data.type === 'sync-complete') {
                // Show sync complete notification
                const results = event.data.results || [];
                const successCount = results.filter(r => r.success).length;
                const failCount = results.length - successCount;
                
                showToast(
                    `Sync complete: ${successCount} items synced${failCount > 0 ? `, ${failCount} failed` : ''}`,
                    successCount > 0 ? 'success' : 'warning'
                );
            }
        });
    }
    
    // Setup IndexedDB for offline data
    setupIndexedDB();
});

// Helper function to show toast notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    
    bsToast.show();
    
    // Remove the toast from DOM after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Setup IndexedDB for offline data
function setupIndexedDB() {
    if (!('indexedDB' in window)) {
        console.warn('IndexedDB not supported. Offline functionality will be limited.');
        return;
    }
    
    const request = indexedDB.open('epetcare-vet-portal-db', 1);
    
    request.onerror = function(event) {
        console.error('IndexedDB error:', event.target.error);
    };
    
    request.onupgradeneeded = function(event) {
        const db = event.target.result;
        
        // Create object stores
        if (!db.objectStoreNames.contains('offline-requests')) {
            db.createObjectStore('offline-requests', { 
                keyPath: 'id',
                autoIncrement: true 
            });
        }
        
        if (!db.objectStoreNames.contains('cache-data')) {
            db.createObjectStore('cache-data', { 
                keyPath: 'key' 
            });
        }
    };
    
    request.onsuccess = function(event) {
        console.log('IndexedDB initialized successfully');
    };
}

// Function to cache data for offline use
function cacheData(key, data) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('epetcare-vet-portal-db', 1);
        
        request.onerror = () => reject(request.error);
        
        request.onsuccess = () => {
            const db = request.result;
            const tx = db.transaction('cache-data', 'readwrite');
            const store = tx.objectStore('cache-data');
            
            store.put({
                key: key,
                data: data,
                timestamp: Date.now()
            });
            
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => reject(tx.error);
        };
    });
}

// Function to get cached data
function getCachedData(key) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('epetcare-vet-portal-db', 1);
        
        request.onerror = () => reject(request.error);
        
        request.onsuccess = () => {
            const db = request.result;
            const tx = db.transaction('cache-data', 'readonly');
            const store = tx.objectStore('cache-data');
            const getRequest = store.get(key);
            
            getRequest.onsuccess = () => {
                if (getRequest.result) {
                    resolve(getRequest.result.data);
                } else {
                    resolve(null);
                }
            };
            
            getRequest.onerror = () => reject(getRequest.error);
        };
    });
}
