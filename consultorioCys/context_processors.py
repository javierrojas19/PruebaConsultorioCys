from .models import Cita

def citas_context_processor(request):
    if request.user.is_authenticated and hasattr(request.user, 'paciente'):
        paciente = request.user.paciente
        citas_activas = Cita.objects.filter(paciente=paciente, confirmado=True, finalizada=0).count()
        cita_existente = Cita.objects.filter(paciente=paciente, confirmado=True, finalizada=0).first()
        return {
            'citas_activas': citas_activas,
            'cita_existente': cita_existente,
        }
    return {}