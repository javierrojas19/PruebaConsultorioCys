from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class UsuarioManager(BaseUserManager):
    def create_user(self, rut, password=None, **extra_fields):
        if not rut:
            raise ValueError('El RUT debe ser proporcionado')
        usuario = self.model(rut=rut, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, rut, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(rut, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    rut = models.CharField(max_length=10, unique=True, primary_key=True)  # RUT del usuario
    email = models.EmailField(unique=True, blank=True, null=True)  # Email opcional
    nombre = models.CharField(max_length=100)  # Nombre del usuario
    apellido = models.CharField(max_length=100)  # Apellido del usuario
    is_active = models.BooleanField(default=True)  # Estado activo/inactivo
    is_staff = models.BooleanField(default=False)  # True si es personal de administración
    
    objects = UsuarioManager()

    USERNAME_FIELD = 'rut'
    REQUIRED_FIELDS = ['email', 'nombre', 'apellido']  # Otros campos requeridos

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rut})"

class Doctor(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    rut_doctor = models.CharField(max_length=10, primary_key=True)  # RUT Doctor
    nombres_doctor = models.CharField(max_length=100)  # Nombre/s Doctor
    primer_apellido_doctor = models.CharField(max_length=50)  # Primer Apellido Doctor
    segundo_apellido_doctor = models.CharField(max_length=50, blank=True)  # Segundo Apellido Doctor
    correo_doctor = models.EmailField(max_length=100)  # Correo Doctor
    telefono_doctor = models.CharField(max_length=15)  # N° Teléfono Doctor
    fecha_nacimiento_doctor = models.DateField(null=True, blank=True)  # Fecha de Nacimiento Doctor
    especialidad_doctor = models.CharField(max_length=100)  # Especialidad Doctor

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctores"

    def __str__(self):
        return f"Dr. {self.nombres_doctor} {self.primer_apellido_doctor}"

class Paciente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    rut_paciente = models.CharField(max_length=10, primary_key=True)  # RUT Paciente
    nombres_paciente = models.CharField(max_length=100)  # Nombre/s Paciente
    primer_apellido_paciente = models.CharField(max_length=50)  # Primer Apellido Paciente
    segundo_apellido_paciente = models.CharField(max_length=50, blank=True)  # Segundo Apellido Paciente
    correo_paciente = models.EmailField(max_length=100)  # Correo Paciente
    telefono_paciente = models.CharField(max_length=15)  # N° Teléfono Paciente
    fecha_nacimiento_paciente = models.DateField(null=True, blank=True)  # Fecha de Nacimiento Paciente
    direccion_paciente = models.CharField(max_length=100, blank=True)  # Dirección Paciente (Opcional)
    archivo = models.FileField(upload_to='archivos_pacientes/', blank=True, null=True)

    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('NB', 'No binario'),
    ]
    genero_paciente = models.CharField(max_length=2, choices=GENDER_CHOICES)  # Género Paciente

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"

    def __str__(self):
        return f"{self.nombres_paciente} {self.primer_apellido_paciente}"

class Clinica(models.Model):
    id_clinica = models.AutoField(primary_key=True)  # ID Clínica
    nombre_clinica = models.CharField(max_length=100)  # Nombre Clínica
    correo_clinica = models.EmailField(max_length=100)  # Correo Clínica
    telefono_clinica = models.CharField(max_length=15)  # N° Teléfono Clínica

    class Meta:
        verbose_name = "Clínica"
        verbose_name_plural = "Clínicas"

    def __str__(self):
        return self.nombre_clinica

class SedeClinica(models.Model):
    id_sede = models.AutoField(primary_key=True)  # ID Sede
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)  # ID Clínica
    region_sede = models.CharField(max_length=30)  # Región Sede
    comuna_sede = models.CharField(max_length=30)  # Comuna Sede
    direccion_sede = models.CharField(max_length=100)  # Dirección Sede
    telefono_sede = models.CharField(max_length=15)  # Teléfono Sede

    class Meta:
        verbose_name = "Sede Clínica"
        verbose_name_plural = "Sedes Clínicas"

    def __str__(self):
        return f"Sede de {self.clinica} en {self.comuna_sede}, {self.region_sede}"

class DoctorClinica(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)  # ID Doctor
    sede = models.ForeignKey(SedeClinica, on_delete=models.CASCADE)  # Relación con SedeClinica en lugar de Clinica

    class Meta:
        unique_together = (('doctor', 'sede'),)
        verbose_name = "Doctor en Sede"
        verbose_name_plural = "Doctores en Sedes"

    def __str__(self):
        return f"{self.doctor} - {self.sede}"
    
class Informe(models.Model):
    id_informe = models.AutoField(primary_key=True)  # ID Informe
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)  # ID Doctor
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)  # ID Paciente
    clinica = models.ForeignKey(Clinica, on_delete=models.SET_NULL, null=True, blank=True)
    sede = models.ForeignKey(SedeClinica, on_delete=models.SET_NULL, null=True, blank=True)
    titulo_informe = models.CharField(max_length=200)  # Título del Informe
    descripcion_informe = models.TextField()  # Descripción del Informe
    notas_doctor = models.TextField(blank=True)  # Notas o comentarios del doctor
    instrucciones_tratamiento = models.TextField(blank=True)  # Instrucciones (medicamentos o tratamientos)
    fecha_informe = models.DateTimeField(auto_now_add=True)  # Fecha del Informe (subido)
    documentos_extra = models.FileField(upload_to='documentos_extra/', blank=True)  # Documentos extras
    

    class Meta:
        verbose_name = "Informe"
        verbose_name_plural = "Informes"

    def __str__(self):
        return f"Informe: {self.titulo_informe} - Paciente: {self.paciente}"


class PacienteInforme(models.Model):
    id_paciente_informe = models.AutoField(primary_key=True)  # ID autoincrementable
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)  # ID Paciente
    informe = models.ForeignKey(Informe, on_delete=models.CASCADE)  # ID Informe
    fecha = models.DateField(auto_now_add=True)  # Fecha

    class Meta:
        verbose_name = "Paciente Informe"
        verbose_name_plural = "Informes de Pacientes"

    def __str__(self):
        return f"Informe de {self.paciente} - ID: {self.informe.id_informe}"
    
    
class Cita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    fecha_cita = models.DateField()
    hora_cita = models.TimeField()
    motivo_consulta = models.CharField(max_length=255, blank=True, null=True)
    confirmado = models.BooleanField(default=False)
    finalizada = models.BooleanField(default=False)

    def __str__(self):
        return f"Cita para {self.paciente.nombres_paciente} con {self.doctor.nombres_doctor} el {self.fecha_cita}"
 
class DisponibilidadDoctor(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    fecha = models.DateField() 
    hora = models.TimeField()
    disponible = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Disponibilidad del Doctor"
        verbose_name_plural = "Disponibilidades de Doctores"
        unique_together = ('doctor', 'fecha', 'hora')

    def __str__(self):
        return f"{self.doctor} - {self.fecha} {self.hora} ({'Disponible' if self.disponible else 'No disponible'})"