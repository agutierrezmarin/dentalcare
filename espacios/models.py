from django.db import models
from django.utils import timezone
from datetime import timedelta


class EspacioClinico(models.Model):
    TIPO_CHOICES = [
        ('sillon',         'Sillón dental'),
        ('consultorio',    'Consultorio general'),
        ('rayos_x',        'Sala de rayos X'),
        ('esterilizacion', 'Sala de esterilización'),
        ('espera',         'Sala de espera'),
        ('cirugia',        'Sala de cirugía'),
        ('laboratorio',    'Laboratorio'),
        ('bodega',         'Bodega'),
        ('oficina',        'Oficina'),
        ('otro',           'Otro'),
    ]

    ESTADO_CHOICES = [
        ('disponible',    'Disponible'),
        ('ocupado',       'Ocupado'),
        ('mantenimiento', 'En mantenimiento'),
        ('inactivo',      'Inactivo'),
    ]

    _PREFIJOS = {
        'sillon':         'S',
        'consultorio':    'C',
        'rayos_x':        'RX',
        'esterilizacion': 'EST',
        'espera':         'ESP',
        'cirugia':        'CIR',
        'laboratorio':    'LAB',
        'bodega':         'BOD',
        'oficina':        'OF',
        'otro':           'E',
    }

    codigo           = models.CharField(max_length=20, unique=True, verbose_name='Código', editable=False)
    nombre           = models.CharField(max_length=150, verbose_name='Nombre')
    tipo             = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sillon')
    descripcion      = models.TextField(blank=True, verbose_name='Descripción')
    ubicacion        = models.CharField(max_length=100, blank=True, verbose_name='Piso / Ubicación')
    capacidad        = models.PositiveSmallIntegerField(default=1, verbose_name='Capacidad (pacientes)')
    color            = models.CharField(max_length=7, default='#22d3ee', verbose_name='Color identificador')
    estado           = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='disponible')
    doctores         = models.ManyToManyField(
        'auth.User',
        blank=True,
        related_name='espacios_asignados',
        verbose_name='Doctores asignados',
    )
    proxima_revision = models.DateField(null=True, blank=True, verbose_name='Próxima revisión')
    activo           = models.BooleanField(default=True)
    creado_en        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['tipo', 'codigo']
        verbose_name = 'Espacio clínico'
        verbose_name_plural = 'Espacios clínicos'

    def save(self, *args, **kwargs):
        if not self.pk and not self.codigo:
            prefix = self._PREFIJOS.get(self.tipo, 'E')
            ultimo = (
                EspacioClinico.objects.filter(codigo__startswith=prefix + '-')
                .order_by('codigo').last()
            )
            if ultimo:
                try:
                    num = int(ultimo.codigo.split('-')[-1]) + 1
                except ValueError:
                    num = 1
            else:
                num = 1
            self.codigo = f"{prefix}-{num:02d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} – {self.nombre}"

    @property
    def revision_vencida(self):
        if not self.proxima_revision:
            return False
        return self.proxima_revision < timezone.now().date()

    @property
    def revision_proxima(self):
        """Revisión en los próximos 7 días (sin estar vencida)."""
        if not self.proxima_revision:
            return False
        hoy = timezone.now().date()
        return hoy <= self.proxima_revision <= hoy + timedelta(days=7)


class MantenimientoEspacio(models.Model):
    TIPO_CHOICES = [
        ('preventivo',  'Mantenimiento preventivo'),
        ('correctivo',  'Mantenimiento correctivo'),
        ('limpieza',    'Limpieza profunda'),
        ('inspeccion',  'Inspección'),
        ('reparacion',  'Reparación de equipo'),
        ('otro',        'Otro'),
    ]

    espacio          = models.ForeignKey(EspacioClinico, on_delete=models.CASCADE, related_name='mantenimientos')
    tipo             = models.CharField(max_length=15, choices=TIPO_CHOICES, default='preventivo')
    descripcion      = models.TextField(verbose_name='Trabajo realizado')
    costo            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    realizado_por    = models.CharField(max_length=200, blank=True, verbose_name='Realizado por')
    fecha            = models.DateField(default=timezone.now)
    proxima_revision = models.DateField(null=True, blank=True, verbose_name='Próxima revisión')
    registrado_por   = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, related_name='+'
    )

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.espacio} – {self.get_tipo_display()} ({self.fecha})"
