const CACHE_NAME = "water-app-v1";

const urlsToCache = [
  "/api/dashboard/",
];

// -----------------------
// PWA Install
// -----------------------
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );

  self.skipWaiting();
});

// -----------------------
// Activate
// -----------------------
self.addEventListener("activate", event => {
  event.waitUntil(self.clients.claim());
});

// -----------------------
// Fetch
// -----------------------
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});