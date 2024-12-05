from django.contrib import admin
from .models import Doctor, Paciente, Informe, Clinica, SedeClinica, DoctorClinica, PacienteInforme, DisponibilidadDoctor


from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    Group.objects.get_or_create(name='Doctor')
    Group.objects.get_or_create(name='Usuario')

admin.site.register(Doctor)
admin.site.register(Paciente)
admin.site.register(Informe)
admin.site.register(Clinica)
admin.site.register(SedeClinica)
admin.site.register(DoctorClinica)
admin.site.register(PacienteInforme)