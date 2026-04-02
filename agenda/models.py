from django.db import models
from pacientes.models import Paciente
from clinico.models import Servicio


class Sillon(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)
    color = models.CharField(max_length=7, default='#22d3ee')

    def __str__(self):
        return self.nombre


class DisponibilidadDoctor(models.Model):
    DIAS = [
        (0,'Lunes'),(1,'Martes'),(2,'Miércoles'),
        (3,'Jueves'),(4,'Viernes'),(5,'Sábado'),(6,'Domingo')
    ]
    doctor = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='disponibilidad')
    dia_semana = models.IntegerField(choices=DIAS)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ['doctor', 'dia_semana']
        ordering = ['dia_semana', 'hora_inicio']

    def __str__(self):
        return f"{self.doctor} - {self.get_dia_semana_display()}"


class BloqueoAgenda(models.Model):
    doctor = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='bloqueos')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    motivo = models.CharField(max_length=200)

    def __str__(self):
        return f"Bloqueo {self.doctor} - {self.fecha}"


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('programada',  'Programada'),
        ('confirmada',  'Confirmada'),
        ('en_curso',    'En curso'),
        ('completada',  'Completada'),
        ('cancelada',   'Cancelada'),
        ('no_asistio',  'No asistió'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    doctor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='citas_doctor')
    sillon = models.ForeignKey(Sillon, on_delete=models.SET_NULL, null=True, blank=True)
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True, blank=True)
    tratamiento = models.ForeignKey(
        'clinico.Tratamiento', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='citas'
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='programada')
    motivo = models.CharField(max_length=300, blank=True)
    notas = models.TextField(blank=True)
    recordatorio_enviado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha', 'hora_inicio']

    def __str__(self):
        return f"{self.paciente} - {self.fecha} {self.hora_inicio}"

    @property
    def duracion_minutos(self):
        from datetime import datetime, date
        inicio = datetime.combine(date.today(), self.hora_inicio)
        fin = datetime.combine(date.today(), self.hora_fin)
        return int((fin - inicio).seconds / 60)
