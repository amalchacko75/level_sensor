from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        try:
            from .create_admin import create_admin
            create_admin()
        except Exception as e:
            print(e)