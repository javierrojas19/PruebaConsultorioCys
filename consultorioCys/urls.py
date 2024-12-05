from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.inicio, name="inicio"),
    path('historial/', views.historial, name="historial"),
    path('acercade/', views.acercade, name="acercade"),
    path('perfil/', views.perfil_view, name="perfil"),
    path('login/', views.login_view, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/doctor/', views.doctor_dashboard, name="doctor_dashboard"),
    path('doctor/add/', views.add_doctor_view, name="add_doctor"),
    path('cambiar_clave/<uidb64>/<token>/', views.cambiar_clave, name='cambiar_clave'),
    path('cambiar_clave_usuario/', views.cambiar_clave_usuario, name='cambiar_clave_usuario'),
    path('restablecer_clave/', views.restablecer_clave, name="restablecer_clave"), 
    path('form_cita/', views.form_cita, name="form_cita"), 
    path('informe_doctores/', views.informe_doctores, name='informe_doctores'),
    path('buscar_paciente/<str:rut_paciente>/', views.buscar_paciente, name='buscar_paciente'),
    path('crear_informe/<str:rut_paciente>/', views.crear_informe, name='crear_informe'),
    path('iniciar_sesion_paciente/<str:rut_paciente>/', views.iniciar_sesion_paciente, name='iniciar_sesion_paciente'),
    path('historial_personal/', views.historial_personal, name='historial_personal'),
    path('pacientes/', views.listar_pacientes, name='listar_pacientes'),
    path('pacientes/nuevo/', views.crear_paciente, name='crear_paciente'),
    path('pacientes/<str:pk>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<str:pk>/eliminar/', views.eliminar_paciente, name='eliminar_paciente'),
    path('pacientes/<str:pk>/informe/', views.informe_paciente, name='informe_paciente'),
    path('paciente_info/<str:rut_paciente>/', views.paciente_info, name='paciente_info'),
    path('ver_calendario/', views.ver_calendario, name='ver_calendario'),
    path('obtener_citas_json/', views.obtener_citas_json, name='obtener_citas_json'),
    path('buscar_doctores/', views.pedir_hora, name='buscar_doctores'),
    path('pedir_hora/', views.pedir_hora, name='pedir_hora'),
    path('seleccionar_doctor/', views.seleccionar_doctor, name='seleccionar_doctor'),
    path('horarios_doctor/<str:doctor_id>/', views.horarios_doctor, name='horarios_doctor'),
    path('informe/<int:pk>/', views.detalle_informe, name='detalle_informe'),
    path("confirmacion_cita/", views.confirmacion_cita, name="confirmacion_cita"),
    path("agendar_cita/", views.agendar_cita, name="agendar_cita"),
    path("resumen_cita/<int:cita_id>/", views.resumen_cita, name="resumen_cita"),
    path('finalizar_cita/<int:cita_id>/', views.finalizar_cita, name='finalizar_cita'),
    path('generar_pdf/<int:informe_id>/', views.generar_pdf, name='generar_pdf'),
    path('descargar_pdf/<path:path>/', views.descargar_como_pdf, name='descargar_como_pdf'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)