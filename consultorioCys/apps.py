from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class ConsultoriocysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'consultorioCys'

    def ready(self):
        post_migrate.connect(create_default_groups, sender=self)

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    from django.contrib.auth.models import Group  # Mover la importación aquí
    Group.objects.get_or_create(name='Doctor')
    Group.objects.get_or_create(name='Usuario')
