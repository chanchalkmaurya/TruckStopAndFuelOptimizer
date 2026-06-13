from django.apps import AppConfig


class FuelConfig(AppConfig):
    name = 'fuel'
    
    def ready(self):
        import fuel.signals
