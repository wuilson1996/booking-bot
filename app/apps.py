from django.apps import AppConfig
from .tasks import iniciar_scheduler

class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        # Importa e inicia la tarea en background
        iniciar_scheduler()