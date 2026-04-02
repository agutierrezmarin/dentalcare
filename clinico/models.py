from django.db import models
from pacientes.models import Paciente


# ─── Catálogo de tratamientos ───────────────────────────────────────────────

class CategoriaServicio(models.Model):
    nombre = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#22d3ee')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = 'Categorías de servicio'


class Servicio(models.Model):
    categoria = models.ForeignKey(CategoriaServicio, on_delete=models.SET_NULL, null=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.IntegerField(default=30)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return self.nombre


# ─── Odontograma ─────────────────────────────────────────────────────────────

class Odontograma(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='odontogramas')
    fecha = models.DateField(auto_now_add=True)
    creado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Odontograma {self.paciente} - {self.fecha}"


class EstadoDiente(models.Model):
    CONDICION_CHOICES = [
        ('sano',         'Sano'),
        ('caries',       'Caries'),
        ('obturado',     'Obturado'),
        ('extraido',     'Extraído'),
        ('corona',       'Corona'),
        ('implante',     'Implante'),
        ('endodoncia',   'Endodoncia'),
        ('fractura',     'Fractura'),
        ('puente',       'Puente'),
        ('ausente',      'Ausente congénito'),
        ('erupcion',     'En erupción'),
    ]
    CARA_CHOICES = [
        ('oclusal',  'Oclusal'),
        ('vestibular','Vestibular'),
        ('lingual',  'Lingual/Palatino'),
        ('mesial',   'Mesial'),
        ('distal',   'Distal'),
        ('general',  'General'),
    ]

    odontograma = models.ForeignKey(Odontograma, on_delete=models.CASCADE, related_name='estados')
    numero_diente = models.IntegerField()  # Notación FDI: 11-48
    condicion = models.CharField(max_length=20, choices=CONDICION_CHOICES, default='sano')
    cara = models.CharField(max_length=15, choices=CARA_CHOICES, default='general')
    notas = models.CharField(max_length=300, blank=True)
    color_hex = models.CharField(max_length=7, default='#22d3ee')

    class Meta:
        unique_together = ['odontograma', 'numero_diente', 'cara']

    def __str__(self):
        return f"Diente {self.numero_diente} - {self.get_condicion_display()}"


# ─── Historia Clínica ─────────────────────────────────────────────────────────

class HistoriaClinica(models.Model):
    paciente = models.OneToOneField(Paciente, on_delete=models.CASCADE, related_name='historia')
    motivo_consulta_inicial = models.TextField(blank=True)
    antecedentes_medicos = models.TextField(blank=True)
    antecedentes_dentales = models.TextField(blank=True)
    habitos = models.TextField(blank=True)
    fecha_apertura = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Historia Clínica - {self.paciente}"


class NotaClinica(models.Model):
    historia = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE, related_name='notas')
    fecha = models.DateTimeField(auto_now_add=True)
    doctor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    motivo = models.CharField(max_length=300)
    hallazgos = models.TextField()
    diagnostico = models.TextField()
    plan_tratamiento = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.historia.paciente} - {self.fecha.date()}"


# ─── Tratamientos ─────────────────────────────────────────────────────────────

class Tratamiento(models.Model):
    ESTADO_CHOICES = [
        ('planificado', 'Planificado'),
        ('en_proceso',  'En proceso'),
        ('completado',  'Completado'),
        ('cancelado',   'Cancelado'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='tratamientos')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    doctor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    numero_diente = models.IntegerField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='planificado')
    precio_acordado = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    notas = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.paciente} - {self.servicio} ({self.get_estado_display()})"

    def get_total_pagado(self):
        from facturacion.models import PlanPago
        return PlanPago.objects.filter(
            tratamiento=self, estado='pagado'
        ).aggregate(t=models.Sum('monto'))['t'] or 0

    def get_saldo_pendiente(self):
        return self.precio_acordado - self.get_total_pagado()
