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

// =====================================================
// Firebase Cloud Messaging
// =====================================================

importScripts(
  "https://www.gstatic.com/firebasejs/11.0.1/firebase-app-compat.js"
);

importScripts(
  "https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging-compat.js"
);

firebase.initializeApp({

  apiKey: "AIzaSyAs4g8X1d-2nBURR_NUCtKuxmKhROfLMDU",

  authDomain: "watertankmonitor-21ef2.firebaseapp.com",

  projectId: "watertankmonitor-21ef2",

  storageBucket: "watertankmonitor-21ef2.firebasestorage.app",

  messagingSenderId: "759777638228",

  appId: "1:759777638228:web:4c7d339052f80a43e07ac1"

});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(payload => {

  console.log("Background Message:", payload);

  self.registration.showNotification(

    payload.notification.title,

    {
      body: payload.notification.body,
      icon: "/static/icon.png",
      badge: "/static/icon.png"
    }

  );

});