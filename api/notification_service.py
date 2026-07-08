import firebase_admin

from firebase_admin import credentials
from firebase_admin import messaging

from django.conf import settings

import os

if not firebase_admin._apps:

    # Render Secret File (production)
    firebase_credentials = os.environ.get(
        "FIREBASE_CREDENTIALS"
    )

    # Local development fallback
    if not firebase_credentials:
        firebase_credentials = os.path.join(
            settings.BASE_DIR,
            "firebase-admin.json"
        )

    cred = credentials.Certificate(firebase_credentials)

    firebase_admin.initialize_app(cred)

def send_notification(token, title, body):

    message = messaging.Message(

        notification=messaging.Notification(
            title=title,
            body=body
        ),

        token=token

    )

    return messaging.send(message)


def check_alerts(level, battery):

    if level >= 95:

        return (
            "Tank Full",
            "Water tank is almost full."
        )

    if level <= 15:

        return (
            "Tank Empty",
            "Water level is very low."
        )

    if battery <= 20:

        return (
            "Battery Low",
            "Battery is below 20%."
        )

    return None