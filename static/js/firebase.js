import { initializeApp } from
"https://www.gstatic.com/firebasejs/11.0.1/firebase-app.js";

import {
    getMessaging,
    getToken,
    onMessage
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

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

Notification.requestPermission()
.then(async (permission) => {

    if (permission !== "granted") {
        console.log("Notification permission denied.");
        return;
    }

    await registerDevice();

});

async function registerDevice() {

    try {

        // Get the existing service worker registration
        const registration = await navigator.serviceWorker.ready;

        const token = await getToken(messaging, {

            vapidKey: "BI_8XFaZsJkkuYy_63aaBPo8Z5Upb4fApwICUumE6iiiwEYPWlRiDglKXe9etH4nW9tjopdvRffF8Pfirf7PxGE",

            serviceWorkerRegistration: registration

        });

        if (!token) {
            console.log("No FCM token received.");
            return;
        }

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

        const result = await response.json();

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