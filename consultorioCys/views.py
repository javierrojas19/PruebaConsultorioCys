from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import AddDoctorForm
from django.contrib.auth import login
from .models import Doctor, Paciente, Informe, Usuario, Clinica, SedeClinica, DoctorClinica, DisponibilidadDoctor
from django.contrib.auth.models import Group, User
from .forms import RUTAuthenticationForm
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm
from django.http import JsonResponse
from .models import Paciente, Informe, Cita
from .forms import PacienteForm, CitaForm, InformeForm
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.http import Http404
from PIL import Image
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import datetime
import random
import string
import os
from .ai_processor import analyze_informe
from django.http import JsonResponse
from django.db.models import Q
from .ai_processor import preprocess_text
from django.core.paginator import Paginator

def handle_form_submission(request, form_class, template_name, success_url, instance=None, authenticate_user=False):
    """Utility function to handle form submissions."""
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            # Solo autenticar si se pasa como parámetro
            if authenticate_user:
                auth_login(request, form.get_user()) if instance is None else None
            return redirect(success_url)
    else:
        form = form_class(instance=instance)
    return render(request, template_name, {'form': form})

def horarios_doctor(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)
    horarios = doctor.horarios_set.all()  # Ajusta esto según el modelo de horarios que tengas
    return render(request, 'horarios_doctor.html', {'doctor': doctor, 'horarios': horarios})

@login_required
def inicio(request):
    message = request.GET.get('message')
    print(f"Usuario autenticado: {request.user.is_authenticated}")

    # Obtener el paciente asociado al usuario autenticado
    paciente = get_object_or_404(Paciente, usuario=request.user)

    # Verificar si el usuario ya tiene una cita confirmada
    cita_existente = Cita.objects.filter(paciente=paciente, confirmado=True).first()

    # Pasar la cita existente al contexto si existe
    return render(request, 'consultorioCys/inicio.html', {
        'message': message,
        'cita_existente': cita_existente
    })

@login_required
def cambiar_clave_usuario(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # Validar la contraseña antigua
        if not user.check_password(old_password):
            messages.error(request, 'La contraseña actual no es correcta.')
            return render(request, 'consultorioCys/cambiar_clave_usuario.html')

        # Validar que las contraseñas nuevas coincidan
        if new_password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'consultorioCys/cambiar_clave_usuario.html')

        # Cambiar la contraseña
        user.password = make_password(new_password)
        user.save()
        messages.success(request, 'La contraseña ha sido cambiada exitosamente.')
        return redirect('perfil')  # Redirigir al perfil del usuario

    return render(request, 'consultorioCys/cambiar_clave_usuario.html')

User = get_user_model()

def cambiar_clave(request, uidb64, token):
    try:
        # Decodificar el UID para obtener al usuario
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        # Validar el token
        if not default_token_generator.check_token(user, token):
            return render(request, 'consultorioCys/cambiar_clave.html', {'error': 'El enlace no es válido o ha expirado.'})

        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                # Cambiar la contraseña
                user.password = make_password(new_password)
                user.save()
                return redirect('login')  # Redirige al login después del cambio exitoso
            else:
                return render(request, 'consultorioCys/cambiar_clave.html', {'error': 'Las contraseñas no coinciden.'})

        return render(request, 'consultorioCys/cambiar_clave.html', {'uidb64': uidb64, 'token': token})
    except (User.DoesNotExist, ValueError, TypeError):
        return render(request, 'consultorioCys/cambiar_clave.html', {'error': 'Ha ocurrido un error. Intenta nuevamente.'})

def restablecer_clave(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            # Enlace para el correo
            domain = request.get_host()
            protocol = 'https' if request.is_secure() else 'http'
            link = f"{protocol}://{domain}/cambiar_clave/{uidb64}/{token}"

            # Renderizar plantilla del correo
            email_subject = 'Restablecimiento de contraseña'
            email_body = render_to_string('consultorioCys/mensaje_cambio_clave.txt', {
                'protocol': protocol,
                'domain': domain,
                'uid': uidb64,
                'token': token,
                'site_name': 'Consultorio Cys',
            })

            # Enviar el correo
            send_mail(
                email_subject,
                email_body,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(request, f"Se ha enviado un mensaje a tu correo {user.email}")
            return render(request, 'consultorioCys/restablecer_clave.html', {'mensaje': 'Correo enviado.'})
        except User.DoesNotExist:
            return render(request, 'consultorioCys/restablecer_clave.html', {'error': 'Correo no encontrado.'})

    return render(request, 'consultorioCys/restablecer_clave.html')

def acercade(request):
    return render(request, 'consultorioCys/acercade.html')

@login_required
def historial_personal(request):
    usuario = request.user

    # Obtener el paciente asociado al usuario autenticado
    paciente = get_object_or_404(Paciente, usuario=usuario)

    # Obtener todos los informes del paciente
    informes = Informe.objects.filter(paciente=paciente).order_by('-fecha_informe')

    # Configurar la paginación
    paginator = Paginator(informes, 10)  # Máximo 10 informes por página
    page_number = request.GET.get('page')  # Obtener el número de página de la URL
    page_obj = paginator.get_page(page_number)  # Obtener la página correspondiente

    # Obtener el informe más reciente (opcional, si se necesita para destacar)
    informe_reciente = informes.first() if informes.exists() else None

    # Obtener las citas futuras del paciente
    citas = Cita.objects.filter(
        paciente=paciente,
        fecha_cita__gte=timezone.now().date()
    ).order_by('fecha_cita', 'hora_cita')

    # Obtener el doctor, clínica y sede del informe más reciente
    doctor = informe_reciente.doctor if informe_reciente else None
    clinica = informe_reciente.clinica if informe_reciente else None
    sede = informe_reciente.sede if informe_reciente else None

    context = {
        'paciente': paciente,
        'informes': page_obj,  # Usar la página actual de informes
        'informe_reciente': informe_reciente,  # Informe más reciente
        'doctor': doctor,
        'clinica': clinica,
        'sede': sede,
        'citas': citas,
    }
    return render(request, 'consultorioCys/historial_personal.html', context)

def detalle_informe(request, pk):
    # Obtener el informe por su ID
    informe = get_object_or_404(Informe, pk=pk)

    return render(request, 'consultorioCys/detalle_informe.html', {'informe': informe})

#AQUI TERMINA EL historial_personal

def historial(request):
    return render(request, 'consultorioCys/historial.html')

@login_required
def resumen_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    return render(request, "consultorioCys/resumen_cita.html", {"cita": cita})

@login_required
def agendar_cita(request):
    if request.method == "POST":
        doctor_id = request.POST.get("doctor_id")
        hora_cita = request.POST.get("hora_cita")
        fecha_cita = request.POST.get("fecha_cita")
        paciente = request.user.paciente  # Asegúrate de que el usuario tenga un perfil de paciente

        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Crea la cita con la información recibida
        nueva_cita = Cita.objects.create(
            paciente=paciente,
            doctor=doctor,
            fecha_cita=fecha_cita,
            hora_cita=hora_cita,
            motivo_consulta=request.POST.get("motivo_consulta", ""),
            confirmado=True
        )

        # Redirige a la página de resumen con el ID de la cita
        return redirect("resumen_cita", cita_id=nueva_cita.id)
    else:
        return redirect("pedir_hora")
    
@login_required
def confirmacion_cita(request):
    # Obtener el paciente asociado al usuario autenticado
    paciente = get_object_or_404(Paciente, usuario=request.user)

    if request.method == 'POST':
        # Procesar la lógica de creación de una nueva cita
        doctor_id = request.POST.get('doctor_id')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')

        # Verificar que los datos requeridos existen
        if not doctor_id or not fecha or not hora:
            return render(request, 'consultorioCys/confirmacion_cita.html', {
                'error': 'Faltan datos necesarios para la confirmación de la cita.'
            })

        # Obtener el doctor y su información
        doctor = get_object_or_404(Doctor, rut_doctor=doctor_id)

        # Convertir la hora al formato HH:MM
        try:
            hora_obj = datetime.datetime.strptime(hora, "%H:%M").time()
        except ValueError:
            return render(request, 'consultorioCys/confirmacion_cita.html', {
                'error': f'El formato de la hora recibido ({hora}) no es válido. Debe estar en el formato HH:MM.'
            })

        # Crear la cita y guardarla en la base de datos
        cita = Cita(
            paciente=paciente,
            doctor=doctor,
            fecha_cita=fecha,
            hora_cita=hora_obj,
            confirmado=True
        )
        cita.save()

        # Obtener la sede asociada al doctor
        doctor_clinica = DoctorClinica.objects.filter(doctor=doctor).first()
        sede = doctor_clinica.sede if doctor_clinica else None

        # Preparar contexto con la información de la nueva cita
        context = {
            'doctor': doctor,
            'fecha': fecha,
            'hora': hora_obj.strftime("%H:%M"),
            'especialidad': doctor.especialidad_doctor,
            'ubicacion': f"{sede.clinica.nombre_clinica} - {sede.comuna_sede}, {sede.region_sede}" if sede else "Ubicación no disponible",
            'citas': Cita.objects.filter(paciente=paciente, finalizada=0).distinct().order_by('fecha_cita', 'hora_cita')
        }

        return render(request, 'consultorioCys/confirmacion_cita.html', context)

    elif request.method == 'GET':
        # Obtener todas las citas activas (finalizada=0) del paciente
        citas = Cita.objects.filter(paciente=paciente, finalizada=0).distinct().order_by('fecha_cita', 'hora_cita')

        # Pasar las citas activas al contexto
        context = {'citas': citas} if citas.exists() else {'error': 'No tienes citas activas en este momento.'}

        return render(request, 'consultorioCys/confirmacion_cita.html', context)

    # Manejo para otros métodos no válidos
    return render(request, 'consultorioCys/confirmacion_cita.html', {
        'error': 'Método de solicitud no válido.'
    })
    
@login_required
def finalizar_cita(request, cita_id):
    # Obtener la cita con el ID proporcionado
    cita = get_object_or_404(Cita, id=cita_id)

    # Verificar que el usuario es un doctor y que es el doctor asignado a la cita
    if not hasattr(request.user, 'doctor') or request.user.doctor != cita.doctor:
        messages.error(request, 'No tienes permiso para finalizar esta cita.')
        return redirect('ver_calendario')  # Redirigir al calendario en caso de error

    # Marcar la cita como finalizada
    cita.finalizada = True
    cita.save()

    # Reactivar la disponibilidad de la hora del doctor en el calendario
    disponibilidad = DisponibilidadDoctor.objects.filter(
        doctor=cita.doctor,
        fecha=cita.fecha_cita,
        hora=cita.hora_cita
    )
    if disponibilidad.exists():
        disponibilidad.update(disponible=True)

    # Enviar un mensaje de confirmación y redirigir al calendario del doctor
    messages.success(request, f'La cita con el paciente {cita.paciente.nombres_paciente} {cita.paciente.primer_apellido_paciente} ha sido finalizada con éxito.')
    return redirect('ver_calendario')  # Cambia esto según dónde desees redirigir al doctor
    
@login_required
def seleccionar_doctor(request):
    especialidad_seleccionada = request.GET.get('especialidad')
    fecha = request.GET.get('fecha')  # Verifica si el parámetro coincide con el nombre del campo del formulario

    print(f"Especialidad seleccionada: {especialidad_seleccionada}")
    print(f"Fecha recibida: {fecha}")  # Esto debería mostrar el valor de la fecha enviada

    doctores = Doctor.objects.filter(especialidad_doctor=especialidad_seleccionada)
    doctores_con_horarios = []

    for doctor in doctores:
        horas_disponibles = DisponibilidadDoctor.objects.filter(
            doctor=doctor,
            fecha=fecha,
            disponible=True
        ).values_list('hora', flat=True)

        doctores_con_horarios.append({
            'doctor': doctor,
            'horas_disponibles': horas_disponibles
        })

    return render(request, 'seleccionar_doctor.html', {
        'doctores': doctores_con_horarios,
        'especialidad': especialidad_seleccionada,
        'fecha': fecha,
    })

@login_required
def pedir_hora(request):
    # Obtener el paciente asociado al usuario autenticado
    paciente = get_object_or_404(Paciente, usuario=request.user)

    # Obtener la cantidad de citas activas
    citas_activas = Cita.objects.filter(paciente=paciente, confirmado=True, finalizada=0).count()

    # Obtener la cita más reciente activa
    cita_existente = Cita.objects.filter(paciente=paciente, confirmado=True, finalizada=0).first()

    # Manejo del límite de citas activas (máximo 3)
    if citas_activas >= 3:
        return render(request, 'confirmacion_cita.html', {
            'mensaje_error': 'No puedes agendar más de 3 citas activas. Cancela alguna para agendar una nueva.',
            'citas_activas': citas_activas,
            'cita_existente': cita_existente,
        })

    # Código para manejar el agendamiento de una nueva cita
    especialidad_seleccionada = request.GET.get('especialidad') or request.POST.get('especialidad')
    sedes = []
    error_message = None

    # Cargar las sedes si se selecciona una especialidad
    if especialidad_seleccionada:
        sedes = SedeClinica.objects.filter(
            doctorclinica__doctor__especialidad_doctor=especialidad_seleccionada
        ).distinct()

    # Validar los campos en el formulario POST (cuando el usuario hace clic en "Buscar Doctores")
    if request.method == 'POST':
        especialidad = request.POST.get('especialidad')
        sede_id = request.POST.get('sede')
        fecha = request.POST.get('fecha')  # Obtener la fecha del formulario

        # Solo redirigir si todos los campos tienen valores
        if especialidad and sede_id and fecha:
            return redirect(
                f"{reverse('seleccionar_doctor')}?especialidad={especialidad}&sede={sede_id}&fecha={fecha}"
            )

        # Mostrar mensaje de error si falta algún campo
        error_message = "Por favor, seleccione la especialidad, la sede y la fecha antes de continuar."

    # Obtener todas las especialidades disponibles
    especialidades = Doctor.objects.values_list('especialidad_doctor', flat=True).distinct()

    # Renderizar la página de pedir hora
    return render(request, 'pedir_hora.html', {
        'especialidades': especialidades,
        'sedes': sedes,
        'especialidad_seleccionada': especialidad_seleccionada,
        'error_message': error_message,
        'citas_activas': citas_activas,
        'cita_existente': cita_existente,
    })

def sedes_por_especialidad(request, especialidad):
    # Filtrar las sedes que tienen doctores con la especialidad seleccionada
    sedes = SedeClinica.objects.filter(
        doctorclinica__doctor__especialidad_doctor=especialidad
    ).distinct()

    sedes_data = [
        {'id': sede.id, 'nombre': sede.nombre_clinica, 'comuna': sede.comuna_sede}
        for sede in sedes
    ]
    
    return JsonResponse({'sedes': sedes_data})

def login_view(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        rut = request.POST.get('rut', '').strip()
        password = request.POST.get('contrasena', '')

        try:
            # Busca el usuario por RUT
            usuario = Usuario.objects.get(rut=rut)

            # Verifica la contraseña
            if usuario.check_password(password):
                # Determina el rol automáticamente
                if Paciente.objects.filter(usuario=usuario).exists():
                    rol = 'paciente'
                    login(request, usuario)
                    return redirect('inicio')
                elif Doctor.objects.filter(usuario=usuario).exists():
                    rol = 'doctor'
                    login(request, usuario)
                    return redirect('doctor_dashboard')
                else:
                    messages.error(request, 'No tienes un rol asignado en el sistema.')
                    return redirect('login')
            else:
                # Si la contraseña es incorrecta
                messages.error(request, 'Contraseña incorrecta.')
                return redirect('login')

        except Usuario.DoesNotExist:
            # Si el RUT no existe en la base de datos
            messages.error(request, 'RUT no se encuentra registrado.')
            return redirect('login')

    # Renderiza el formulario de login
    return render(request, 'consultorioCys/login.html')

@login_required
def perfil_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')

        usuario = request.user

        # Actualizar datos comunes
        if email:
            usuario.email = email

        # Si el usuario es un doctor
        if hasattr(usuario, 'doctor'):
            doctor = usuario.doctor
            if telefono:
                doctor.telefono_doctor = telefono
            doctor.save()

        # Si el usuario es un paciente
        elif hasattr(usuario, 'paciente'):
            paciente = usuario.paciente
            if telefono:
                paciente.telefono_paciente = telefono
            if direccion:
                paciente.direccion_paciente = direccion
            paciente.save()

        usuario.save()
        messages.success(request, 'Tus datos han sido actualizados exitosamente.')
        return redirect('perfil')

    return render(request, 'consultorioCys/perfil.html', {
        'usuario': request.user,
        'doctor': getattr(request.user, 'doctor', None),
        'paciente': getattr(request.user, 'paciente', None),
    })


def logout_view(request):
    logout(request)
    return redirect('inicio')

def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

@login_required
@user_passes_test(is_doctor)
def doctor_dashboard(request):
    if request.user.is_authenticated and isinstance(request.user, Doctor):
        return render(request, 'consultorioCys/doctor_dashboard.html', {'doctor': request.user})
    return redirect('login')

def is_paciente(user):
    return user.groups.filter(name='Paciente').exists()

@login_required
def doctor_dashboard(request):
    if hasattr(request.user, 'paciente'):
        messages.error(request, 'No tienes permisos para acceder a esta sección como paciente.')
        return redirect('inicio')
    
    # Si el usuario es doctor, muestra el dashboard
    return render(request, 'consultorioCys/doctor_dashboard.html')

@login_required
def paciente_dashboard(request):
    print("Entrando al dashboard del paciente")
    return render(request, 'consultorioCys/paciente_dashboard.html')

def is_usuario(user):
    return user.groups.filter(name='Usuario').exists()

def is_doctor(user):
    return user.groups.filter(name='Doctor').exists()

@login_required
@user_passes_test(is_doctor)
def add_doctor_view(request):
    if request.method == 'POST':
        form = AddDoctorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('doctor_dashboard')  # Redirigir a algún lugar después de agregar el doctor
    else:
        form = AddDoctorForm()
    return render(request, 'consultorioCys/add_doctor.html', {'form': form})

def informe_doctores(request):
    # Obtener todos los doctores desde la base de datos
    doctores = Doctor.objects.all()

    # Pasar los datos de los doctores a la plantilla 'informe_doctores.html'
    return render(request, 'informe_doctores.html', {'doctores': doctores})

def paciente_info(request, rut_paciente):
    # Buscar el paciente usando `rut_paciente`
    paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)

    # Obtener los informes relacionados usando `informe_set`
    informes = paciente.informe_set.all().order_by('-fecha_informe')

    return render(request, 'consultorioCys/paciente_info.html', {
        'paciente': paciente,
        'informes': informes,
    })

# Buscar pacientes
@login_required
def buscar_paciente(request, rut_paciente=None):
    if rut_paciente:
        try:
            paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)
            informes = Informe.objects.filter(paciente=paciente).order_by('-fecha_informe')

            # Obtener la cita activa (confirmada y no finalizada) asociada al doctor autenticado
            cita_activa = Cita.objects.filter(
                paciente=paciente,
                doctor=request.user.doctor,
                finalizada=False
            ).first()

            # Guardar el diagnóstico seleccionado
            if request.method == 'POST' and 'selected_diagnosis' in request.POST:
                informe_id = request.POST.get('informe_id')
                selected_diagnosis = request.POST.get('selected_diagnosis')

                # Obtener el nombre del doctor
                if hasattr(request.user, 'doctor'):
                    doctor_name = f"{request.user.doctor.nombres_doctor} {request.user.doctor.primer_apellido_doctor}"
                else:
                    doctor_name = "Doctor desconocido"

                try:
                    informe = get_object_or_404(Informe, id_informe=informe_id)

                    # Guardar el diagnóstico seleccionado y registrar su origen
                    informe.notas_doctor = f"Diagnóstico seleccionado: {selected_diagnosis} (por: {doctor_name})"
                    informe.save()

                    messages.success(request, "Diagnóstico aplicado correctamente.")
                    return redirect('buscar_paciente', rut_paciente=rut_paciente)
                except Informe.DoesNotExist:
                    messages.error(request, "El informe seleccionado no existe.")

            # Analizar cada informe y generar diagnósticos sugeridos
            for informe in informes:
                # Llamar a la función de análisis
                analysis_result = analyze_informe(informe.descripcion_informe)

                # Diagnóstico más probable
                most_probable = analysis_result["most_probable"]
                confidence = analysis_result["confidence"]
                alternatives = analysis_result["alternatives"]

                # Diagnósticos de la IA etiquetados
                ia_diagnoses = [
                    {"text": f"{alt['diagnosis']} (sugerido por IA)", "confidence": alt["confidence"]}
                    for alt in alternatives
                ]

                # Incluir el diagnóstico del doctor como opción
                doctor_diagnosis = [
                    {"text": f"{informe.notas_doctor or 'Sin diagnóstico previo'} (actual del doctor)", "confidence": None}
                ]

                # Combinar diagnósticos
                informe.diagnosis_suggestions = doctor_diagnosis + ia_diagnoses

            return render(request, 'consultorioCys/buscar_paciente.html', {
                'paciente': paciente,
                'informes': informes,
                'cita_activa': cita_activa,  # Pasar la cita activa al contexto
            })
        except Paciente.DoesNotExist:
            messages.error(request, "Este RUT no corresponde a un paciente.")
            return redirect('doctor_dashboard')

    return redirect('doctor_dashboard')

# Listado de pacientes
def listar_pacientes(request):
    pacientes = Paciente.objects.prefetch_related('informe_set')
    pacientes = Paciente.objects.all()
    return render(request, 'pacientes_list.html', {'pacientes': pacientes})

# Crear un nuevo paciente
Usuario = get_user_model()
def crear_paciente(request):
    if request.method == 'POST':
        # Recopilar datos del formulario
        rut = request.POST.get('rut')
        nombres = request.POST.get('nombres')
        primer_apellido = request.POST.get('primer_apellido')
        segundo_apellido = request.POST.get('segundo_apellido')
        correo = request.POST.get('correo')
        telefono = request.POST.get('telefono')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        direccion = request.POST.get('direccion')
        genero = request.POST.get('genero')
        archivo = request.FILES.get('archivo')

        # Generar una contraseña aleatoria
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        try:
            # Crear el usuario
            usuario = Usuario.objects.create_user(
                rut=rut,
                email=correo,
                password=password,
                nombre=nombres,
                apellido=primer_apellido,
            )

            # Crear el paciente asociado
            paciente = Paciente.objects.create(
                usuario=usuario,
                rut_paciente=rut,
                nombres_paciente=nombres,
                primer_apellido_paciente=primer_apellido,
                segundo_apellido_paciente=segundo_apellido,
                correo_paciente=correo,
                telefono_paciente=telefono,
                fecha_nacimiento_paciente=fecha_nacimiento,
                direccion_paciente=direccion,
                genero_paciente=genero,
                archivo=archivo,
            )

            # Opcional: Enviar mensaje al usuario (correo con la contraseña generada)
            # Aquí puedes integrar una función para enviar la contraseña al correo.

            messages.success(request, f"El paciente {nombres} ha sido registrado con éxito. Contraseña: {password}")
            return redirect('listar_pacientes')  # Redirigir a la vista que corresponda
        except Exception as e:
            messages.error(request, f"Error al registrar el paciente: {e}")
            return redirect('crear_paciente')

    return render(request, 'consultorioCys/crear_paciente.html')

# Editar un paciente existente
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        form = PacienteForm(request.POST, request.FILES, instance=paciente)
        if form.is_valid():
            form.save()
            return redirect('listar_pacientes')
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'paciente_form.html', {'form': form})

# Eliminar un paciente
def eliminar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == "POST":
        paciente.delete()
        return redirect('listar_pacientes')
    return render(request, 'confirmar_eliminar.html', {'paciente': paciente})

def informe_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    informes = Informe.objects.filter(paciente=paciente)  # Trae todos los informes del paciente
    edit_informe_id = request.POST.get('edit_informe_id')  # Identificador del informe que se va a editar

    if request.method == 'POST' and edit_informe_id:  # Si se está enviando el formulario de edición
        informe = get_object_or_404(Informe, id=edit_informe_id)
        form = InformeForm(request.POST, request.FILES, instance=informe)
        if form.is_valid():
            form.save()
            return redirect('informe_paciente', pk=paciente.pk)  # Refresca la página
    else:
        form = InformeForm()  # Formulario vacío si no estamos editando
    
    return render(request, 'informe_paciente.html', {'paciente': paciente, 'informes': informes, 'form': form})

@login_required
def crear_informe(request, rut_paciente):
    doctor = get_object_or_404(Doctor, usuario=request.user)
    paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)

    # Obtener la clínica y sede asociada al doctor
    doctor_clinica = DoctorClinica.objects.filter(doctor=doctor).first()
    clinica = doctor_clinica.sede.clinica if doctor_clinica else None
    sede = doctor_clinica.sede if doctor_clinica else None

    if request.method == 'POST':
        form = InformeForm(request.POST, request.FILES)
        if form.is_valid():
            informe = form.save(commit=False)  # No guardar aún
            informe.doctor = doctor  # Asignar el doctor automáticamente
            informe.paciente = paciente  # Asignar el paciente
            informe.clinica = clinica  # Asignar la clínica
            informe.sede = sede  # Asignar la sede
            informe.save()  # Guardar el informe
            messages.success(request, "El informe se creó exitosamente.")
            # Redirigir correctamente con el argumento necesario
            return redirect('buscar_paciente', rut_paciente=paciente.rut_paciente)
        else:
            print("Errores del formulario:", form.errors)
            messages.error(request, "Error al procesar el formulario. Verifica los datos ingresados.")
    else:
        form = InformeForm()

    return render(request, 'consultorioCys/crear_informe.html', {
        'form': form,
        'paciente': paciente
    })

#formulario agendar cita y calendario en doctor 
def form_cita(request):
    # Verificar que el usuario autenticado es un paciente
    try:
        paciente = Paciente.objects.get(usuario=request.user)
    except Paciente.DoesNotExist:
        messages.error(request, 'Solo los pacientes pueden solicitar citas.')
        return redirect('inicio')  # Redirige a la página de inicio si no es paciente

    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            # Crear una nueva cita
            cita = form.save(commit=False)
            cita.paciente = paciente  # Asigna el paciente actual a la cita

            # Si el paciente ya tiene un doctor asignado, lo agregamos a la cita
            if Doctor.objects.filter(usuario=request.user).exists():
                cita.doctor = Doctor.objects.get(usuario=request.user)
            
            # Guardar la cita y confirmar
            cita.save()
            messages.success(request, 'Su cita ha sido solicitada con éxito.')
            return redirect('inicio')
    else:
        form = CitaForm()

    return render(request, 'consultorioCys/form_cita.html', {'form': form})


@login_required
def ver_calendario(request):
    # Obtener el médico asociado al usuario autenticado
    doctor = Doctor.objects.get(usuario=request.user)

    # Obtener las citas confirmadas de la base de datos
    citas = Cita.objects.filter(doctor=doctor, confirmado=True)

    # Formatear los datos en el backend para pasarlos al template
    eventos = [
        {
            'title': f"{cita.paciente.nombres_paciente} {cita.paciente.primer_apellido_paciente}",
            'start': f"{cita.fecha_cita}T{cita.hora_cita}",
            'end': f"{cita.fecha_cita}T{(datetime.datetime.combine(cita.fecha_cita, cita.hora_cita) + datetime.timedelta(minutes=30)).time()}",
            'className': 'evento-finalizado' if cita.finalizada else 'evento-pendiente',  # Clase CSS según el estado
            'extendedProps': {
                'tratamiento': cita.motivo_consulta or "Consulta General",
                'rut_paciente': cita.paciente.rut_paciente,  # Pasar el RUT del paciente
            },
        }
        for cita in citas
    ]
    # Pasar los eventos como contexto al template
    return render(request, 'consultorioCys/ver_calendario.html', {'eventos': eventos})

@login_required
def iniciar_sesion_paciente(request, rut_paciente):
    paciente = get_object_or_404(Paciente, rut_paciente=rut_paciente)

    if request.method == 'POST':
        clave_ingresada = request.POST.get('clave')
        if paciente.usuario.check_password(clave_ingresada):
            return redirect('buscar_paciente', rut_paciente=rut_paciente)
        else:
            messages.error(request, "Contraseña incorrecta. Intente de nuevo.")

    return render(request, 'consultorioCys/iniciar_sesion_paciente.html', {'paciente': paciente})

@login_required
def obtener_citas_json(request):
    # Obtener el doctor asociado al usuario autenticado
    doctor = Doctor.objects.get(usuario=request.user)

    # Filtrar citas confirmadas
    citas = Cita.objects.filter(doctor=doctor, confirmado=True)

    # Formatear eventos
    eventos = []
    for cita in citas:
        eventos.append({
            'title': f"{cita.hora_cita.strftime('%H:%M')} {cita.paciente.nombres_paciente} {cita.paciente.primer_apellido_paciente}",
            'start': f"{cita.fecha_cita}T{cita.hora_cita}",
            'color': '#007bff',  # Azul personalizado
        })

    return JsonResponse(eventos, safe=False)

@login_required
def generar_pdf(request, informe_id):
    # Obtener el informe desde la base de datos
    informe = get_object_or_404(Informe, id_informe=informe_id)

    # Configuración del archivo PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="informe_{informe.id_informe}.pdf"'

    # Crear el PDF
    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Ruta del logo
    logo_path = os.path.join(settings.MEDIA_ROOT, 'img/logo-png.png')

    # Encabezado con logo
    if os.path.exists(logo_path):
        pdf.drawImage(logo_path, 50, height - 100, width=100, height=100)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, height - 50, "INFORME MÉDICO")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(200, height - 70, f"Emitido por: {informe.doctor.nombres_doctor} {informe.doctor.primer_apellido_doctor}")
    pdf.drawString(200, height - 85, f"Especialidad: {informe.doctor.especialidad_doctor}")
    pdf.drawString(200, height - 100, f"Teléfono: {informe.doctor.telefono_doctor}")

    # Línea divisoria
    pdf.line(50, height - 120, 550, height - 120)

    # Información del paciente
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 140, "Datos del Paciente")
    patient_data = [
        ["Nombre:", f"{informe.paciente.nombres_paciente} {informe.paciente.primer_apellido_paciente}"],
        ["RUT:", informe.paciente.rut_paciente],
        ["Género:", informe.paciente.get_genero_paciente_display()],
        ["Fecha de Nacimiento:", informe.paciente.fecha_nacimiento_paciente.strftime('%d-%m-%Y')],
        ["Teléfono:", informe.paciente.telefono_paciente],
        ["Dirección:", informe.paciente.direccion_paciente]
    ]

    table = Table(patient_data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    table.wrapOn(pdf, width, height)
    table.drawOn(pdf, 50, height - 300)

    # Información del informe
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, height - 320, "Datos del Informe")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, height - 340, f"Título: {informe.titulo_informe}")
    pdf.drawString(50, height - 360, f"Fecha: {informe.fecha_informe.strftime('%d-%m-%Y')}")
    pdf.drawString(50, height - 380, "Descripción:")
    pdf.setFont("Helvetica", 10)

    y = height - 400
    for line in informe.descripcion_informe.split('\n'):
        pdf.drawString(70, y, line)
        y -= 15
        if y < 100:
            pdf.showPage()
            y = height - 50

    # Diagnóstico Seleccionado
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y - 20, "Diagnóstico Seleccionado:")
    pdf.setFont("Helvetica", 10)
    y -= 40
    diagnosis_text = informe.notas_doctor or "Sin diagnóstico disponible."
    for line in diagnosis_text.split('\n'):
        pdf.drawString(70, y, line)
        y -= 15
        if y < 100:
            pdf.showPage()
            y = height - 50

    # Pie de página con información de la clínica
    pdf.setFont("Helvetica", 10)
    footer_y_position = 50
    if informe.clinica and informe.sede:
        pdf.drawString(50, footer_y_position, f"Consultorio Cys - {informe.clinica.nombre_clinica}")
        pdf.drawString(50, footer_y_position - 10, f"Dirección: {informe.sede.direccion_sede}, {informe.sede.comuna_sede}, {informe.sede.region_sede} - Teléfono: {informe.sede.telefono_sede}")
    else:
        pdf.drawString(50, footer_y_position, "Consultorio Cys")
        pdf.drawString(50, footer_y_position - 10, "Dirección: No disponible")

    # Guardar el PDF
    pdf.save()
    return response

def descargar_como_pdf(request, path):
    # Ruta del archivo original
    file_path = os.path.join(settings.MEDIA_ROOT, path)
    if not os.path.exists(file_path):
        raise Http404("El archivo no existe.")

    # Configurar la respuesta como PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{os.path.splitext(os.path.basename(path))[0]}.pdf"'

    # Crear el objeto canvas
    pdf = canvas.Canvas(response, pagesize=letter)

    # Si es una imagen, incluirla en el PDF
    try:
        img = Image.open(file_path)
        img_width, img_height = img.size

        # Escalar la imagen para ajustarse al tamaño del PDF
        page_width, page_height = letter
        scale = min(page_width / img_width, page_height / img_height)
        img_width = int(img_width * scale)
        img_height = int(img_height * scale)

        # Dibujar la imagen en el PDF
        pdf.drawImage(file_path, 0, page_height - img_height, img_width, img_height)

    except Exception:
        # Si no es una imagen, simplemente incluir el nombre del archivo en el PDF
        pdf.drawString(100, 750, "El archivo no es compatible para incrustar directamente en PDF.")
        pdf.drawString(100, 730, f"Archivo original: {os.path.basename(path)}")

    # Finalizar y cerrar el PDF
    pdf.showPage()
    pdf.save()

    return response