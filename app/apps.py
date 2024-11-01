from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        # Importa e inicia la tarea en background
        from .tasks import iniciar_tarea_diaria
        iniciar_tarea_diaria()