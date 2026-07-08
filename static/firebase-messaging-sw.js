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

    self.registration.showNotification(
        payload.notification.title,
        {
            body: payload.notification.body,
            icon: "/static/icons/icon-192.png"
        }
    );

});