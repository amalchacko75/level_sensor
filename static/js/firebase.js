import { initializeApp } from "https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";

import {
    getMessaging,
    getToken,
    onMessage,
    isSupported
} from "https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging.js";

/* -------------------------------------------------------
   Firebase Configuration
------------------------------------------------------- */

const firebaseConfig = {
  apiKey: "AIzaSyAs4g8X1d-2nBURR_NUCtKuxmKhROfLMDU",
  authDomain: "watertankmonitor-21ef2.firebaseapp.com",
  projectId: "watertankmonitor-21ef2",
  storageBucket: "watertankmonitor-21ef2.firebasestorage.app",
  messagingSenderId: "759777638228",
  appId: "1:759777638228:web:4c7d339052f80a43e07ac1"
};

/* -------------------------------------------------------
   Initialize Firebase
------------------------------------------------------- */

const supported = await isSupported();

if (!supported) {

    console.log("Firebase Messaging is not supported.");

    throw new Error("Firebase Messaging not supported.");

}

const app = initializeApp(firebaseConfig);

const messaging = getMessaging(app);

/* -------------------------------------------------------
   Startup Logs
------------------------------------------------------- */

console.log("Firebase Messaging Ready");

console.log("Permission:", Notification.permission);

console.log("Standalone:",
    window.matchMedia("(display-mode: standalone)").matches);

console.log("User Agent:",
    navigator.userAgent);

/* -------------------------------------------------------
   Wait for DOM
------------------------------------------------------- */

const button = document.getElementById("enableNotifications");

console.log("Button:", button);

if (!button) {
    console.error("Button not found");
} else {

    if (Notification.permission === "granted") {

        button.style.display = "none";

        registerDevice();

    } else {

        button.onclick = async () => {

            console.log("Button clicked");

            const permission = await Notification.requestPermission();

            console.log("Permission:", permission);

            if (permission !== "granted")
                return;

            await registerDevice();

            button.innerHTML = "✅ Notifications Enabled";
            button.disabled = true;
        };

    }
}

/* -------------------------------------------------------
   Register Device
------------------------------------------------------- */

async function registerDevice() {

    console.log("registerDevice() called");

    try {

        console.log("Waiting for service worker...");

        const registration = await navigator.serviceWorker.ready;

        console.log("Service Worker Ready", registration);

        console.log("Calling getToken()...");

        const token = await getToken(messaging, {
            vapidKey: "BI_8XFaZsJkkuYy_63aaBPo8Z5Upb4fApwICUumE6iiiwEYPWlRiDglKXe9etH4nW9tjopdvRffF8Pfirf7PxGE",
            serviceWorkerRegistration: registration
        });

        console.log("getToken finished");

        if (!token) {
            console.log("No token received.");
            return;
        }

        console.log("FCM Token:", token);

        console.log("Calling save-token API...");

        const response = await fetch("/api/save-token/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                token: token,
                device_type: getDeviceType()
            })
        });

        console.log("Response status:", response.status);

        const result = await response.json();

        console.log(result);

    } catch (err) {

        console.error("registerDevice failed:", err);

    }

}

/* -------------------------------------------------------
   Foreground Notification
------------------------------------------------------- */

onMessage(messaging, payload => {

    console.log("Foreground Notification");

    console.log(payload);

    new Notification(

        payload.notification.title,

        {

            body:
                payload.notification.body,

            icon:
                "/static/icons/icon-192.png",

            badge:
                "/static/icons/icon-192.png"

        }

    );

});

/* -------------------------------------------------------
   Device Type
------------------------------------------------------- */

function getDeviceType() {

    const ua =
        navigator.userAgent.toLowerCase();

    if (/iphone|ipad|ipod/.test(ua))
        return "ios";

    if (/android/.test(ua))
        return "android";

    return "web";

}