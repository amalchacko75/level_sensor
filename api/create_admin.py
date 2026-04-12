from django.contrib.auth.models import User

def create_admin():
    User.objects.filter(username="admin").delete()

    User.objects.create_superuser(
        username="admin",
        email="your_email@gmail.com",
        password="admin123"
    )