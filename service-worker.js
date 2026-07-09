/* ==========================================================
   Water Tank Monitor
   Service Worker
   PWA + Firebase Cloud Messaging
========================================================== */

const CACHE_NAME = "water-monitor-v1";

/* ----------------------------------------------------------
   Files to cache
---------------------------------------------------------- */

const FILES_TO_CACHE = [];

/* ----------------------------------------------------------
   Install
---------------------------------------------------------- */

self.addEventListener("install", event => {

    console.log("Service Worker Installed");

    self.skipWaiting();

});

/* ----------------------------------------------------------
   Activate
---------------------------------------------------------- */

self.addEventListener("activate", event => {

    console.log("Service Worker Activated");

    event.waitUntil(
        self.clients.claim()
    );

});

/* ----------------------------------------------------------
   Fetch
---------------------------------------------------------- */

self.addEventListener("fetch", event => {

    if (event.request.method !== "GET") {
        return;
    }

    event.respondWith(
        fetch(event.request)
    );

});

/* ==========================================================
   Firebase
========================================================== */

importScripts(
    "https://www.gstatic.com/firebasejs/11.0.1/firebase-app-compat.js"
);

importScripts(
    "https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging-compat.js"
);

/* ----------------------------------------------------------
   Firebase Config
---------------------------------------------------------- */

firebase.initializeApp({

  apiKey: "AIzaSyAs4g8X1d-2nBURR_NUCtKuxmKhROfLMDU",

  authDomain: "watertankmonitor-21ef2.firebaseapp.com",

  projectId: "watertankmonitor-21ef2",

  storageBucket: "watertankmonitor-21ef2.firebasestorage.app",

  messagingSenderId: "759777638228",

  appId: "1:759777638228:web:4c7d339052f80a43e07ac1"

});

/* ----------------------------------------------------------
   Messaging
---------------------------------------------------------- */

const messaging = firebase.messaging();

/* ----------------------------------------------------------
   Background Notification
---------------------------------------------------------- */

messaging.onBackgroundMessage(payload => {

    console.log("Background Notification:", payload);

    const notificationTitle =
        payload.notification?.title || "Water Tank Monitor";

    const notificationOptions = {

        body:
            payload.notification?.body || "",

        icon:
            "/static/icons/icon-192.png",

        badge:
            "/static/icons/icon-192.png",

        vibrate: [200, 100, 200],

        requireInteraction: true,

        data: {

            url: "/api/dashboard/"

        }

    };

    self.registration.showNotification(

        notificationTitle,

        notificationOptions

    );

});

/* ----------------------------------------------------------
   Notification Click
---------------------------------------------------------- */

self.addEventListener("notificationclick", event => {

    event.notification.close();

    event.waitUntil(

        clients.matchAll({

            type: "window",

            includeUncontrolled: true

        })

        .then(clientList => {

            for (const client of clientList) {

                if ("focus" in client) {

                    client.navigate("/api/dashboard/");

                    return client.focus();

                }

            }

            return clients.openWindow("/api/dashboard/");

        })

    );

});