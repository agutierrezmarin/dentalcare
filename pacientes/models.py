from django.db import models
from django.utils import timezone


class Paciente(models.Model):
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    TIPO_SANGRE = [
        ('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
        ('AB+','AB+'),('AB-','AB-'),('O+','O+'),('O-','O-'),('?','Desconocido')
    ]

    # Datos personales
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, default='M')
    ci = models.CharField('C.I.', max_length=20, unique=True, null=True, blank=True)
    tipo_sangre = models.CharField(max_length=3, choices=TIPO_SANGRE, default='?')

    # Contacto
    telefono = models.CharField(max_length=20, blank=True)
    telefono_emergencia = models.CharField(max_length=20, blank=True)
    contacto_emergencia = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)

    # Historial médico
    alergias = models.TextField(blank=True)
    medicamentos_actuales = models.TextField(blank=True)
    enfermedades_cronicas = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)

    # Sistema
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    foto = models.ImageField(upload_to='pacientes/fotos/', null=True, blank=True)

    class Meta:
        ordering = ['apellidos', 'nombres']
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def edad(self):
        if self.fecha_nacimiento:
            hoy = timezone.now().date()
            return (hoy - self.fecha_nacimiento).days // 365
        return None

    def get_deuda_pendiente(self):
        from facturacion.models import PlanPago
        total = PlanPago.objects.filter(
            tratamiento__paciente=self,
            estado='pendiente'
        ).aggregate(
            total=models.Sum('monto')
        )['total'] or 0
        return total


class Alergia(models.Model):
    TIPO_CHOICES = [
        ('medicamento', 'Medicamento'),
        ('material', 'Material dental'),
        ('alimento', 'Alimento'),
        ('otro', 'Otro'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='lista_alergias')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.CharField(max_length=200)
    reaccion = models.TextField(blank=True)
    gravedad = models.CharField(max_length=10, choices=[
        ('leve','Leve'),('moderada','Moderada'),('severa','Severa')
    ], default='leve')

    def __str__(self):
        return f"{self.paciente} - {self.descripcion}"


class AdjuntoPaciente(models.Model):
    TIPO_CHOICES = [
        ('radiografia', 'Radiografía'),
        ('foto', 'Fotografía clínica'),
        ('documento', 'Documento'),
        ('consentimiento', 'Consentimiento informado'),
        ('otro', 'Otro'),
    ]
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='adjuntos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    archivo = models.FileField(upload_to='pacientes/adjuntos/%Y/%m/')
    descripcion = models.TextField(blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.paciente} - {self.titulo}"
