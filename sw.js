const CACHE_NAME = 'japanese-coach-v1'
const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/js/app.js',
  '/js/supabase.js',
  '/js/auth.js',
  '/js/groq.js',
  '/js/habitica.js',
  '/css/styles.css',
]

// 安裝：快取靜態資源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache)
    })
  )
})

// 激活：清除舊快取
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    })
  )
})

// 攔截請求：快取優先，網路備援
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) return response
      
      return fetch(event.request).then((response) => {
        // 只快取靜態資源，不快取 API 請求
        if (!event.request.url.includes('supabase.co') && 
            !event.request.url.includes('habitica.com') && 
            !event.request.url.includes('groq.com')) {
          const responseToCache = response.clone()
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache)
          })
        }
        return response
      })
    })
  )
})
