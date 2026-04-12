from django.contrib.auth.models import User

def create_admin():
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="your_email@gmail.com",
            password="admin123"
        )