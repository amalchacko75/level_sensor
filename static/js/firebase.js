import { initializeApp } from
"https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";

import {
    getMessaging,
    getToken,
    onMessage,
    isSupported
} from
"https://www.gstatic.com/firebasejs/11.0.1/firebase-messaging.js";

const firebaseConfig = {
  apiKey: "AIzaSyAs4g8X1d-2nBURR_NUCtKuxmKhROfLMDU",
  authDomain: "watertankmonitor-21ef2.firebaseapp.com",
  projectId: "watertankmonitor-21ef2",
  storageBucket: "watertankmonitor-21ef2.firebasestorage.app",
  messagingSenderId: "759777638228",
  appId: "1:759777638228:web:4c7d339052f80a43e07ac1"
};
const supported = await isSupported();
if (!supported) {
    console.log("Firebase Messaging is not supported on this browser.");
    throw new Error("Firebase Messaging not supported");
}
const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

console.log("Current Permission:", Notification.permission);
console.log("User Agent:", navigator.userAgent);

console.log("Standalone Mode:", window.matchMedia('(display-mode: standalone)').matches);

console.log("Notification Permission:", Notification.permission);

async function registerDevice() {

    console.log("registerDevice() started");
    try {

        // Get the existing service worker registration
        console.log("Waiting for Service Worker...");
        const registration = await navigator.serviceWorker.ready;

        console.log("Using Service Worker:", registration);

        const token = await getToken(messaging, {

            vapidKey: "BI_8XFaZsJkkuYy_63aaBPo8Z5Upb4fApwICUumE6iiiwEYPWlRiDglKXe9etH4nW9tjopdvRffF8Pfirf7PxGE",

            serviceWorkerRegistration: registration

        });
        console.log("Token Result:", token);

        if (!token) {
            console.log("No FCM token received.");
            return;
        }
        console.log("Saving token...");
        console.log("FCM Token:", token);

        // Save the token to Django
        const response = await fetch("/api/save-token/", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                token: token
            })

        });
        console.log("Response Status:", response.status);
        const result = await response.json();
        if (!response.ok) {
            console.error("Failed to save token:", result);
            return;
        }
        console.log("Token saved:", result);

    } catch (error) {

        console.error("FCM Error:", error);

    }

}

// Foreground notifications
onMessage(messaging, (payload) => {

    console.log("Foreground message:", payload);

    new Notification(
        payload.notification.title,
        {
            body: payload.notification.body,
            icon: "/static/icon.png"
        }
    );

});

document.addEventListener("DOMContentLoaded", async () => {

    console.log("DOM Ready");

    const button = document.getElementById("enableNotifications");

    if (!button) {
        console.log("Button not found");
        return;
    }

    if (Notification.permission === "granted") {

        button.style.display = "none";

        await registerDevice();

        return;
    }

    button.onclick = async () => {

        console.log("Button clicked");

        const permission = await Notification.requestPermission();

        if (permission !== "granted")
            return;

        await registerDevice();

        button.innerHTML = "✅ Notifications Enabled";
        button.disabled = true;

    };

});