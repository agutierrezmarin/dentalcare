from django.db import models
from django.utils import timezone
from datetime import timedelta


class CategoriaInsumo(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Insumo(models.Model):
    UNIDAD_CHOICES = [
        ('unidad',   'Unidad'),
        ('caja',     'Caja'),
        ('frasco',   'Frasco'),
        ('rollo',    'Rollo'),
        ('par',      'Par'),
        ('ml',       'Mililitros'),
        ('gr',       'Gramos'),
        ('tableta',  'Tableta'),
        ('ampolla',  'Ampolla'),
        ('tubo',     'Tubo'),
        ('sobre',    'Sobre'),
        ('litro',    'Litro'),
        ('kg',       'Kilogramo'),
        ('jeringa',  'Jeringa'),
        ('guante',   'Par de guantes'),
    ]

    categoria       = models.ForeignKey(CategoriaInsumo, on_delete=models.SET_NULL, null=True, blank=True)
    nombre          = models.CharField(max_length=200)
    descripcion     = models.TextField(blank=True)
    unidad          = models.CharField(max_length=10, choices=UNIDAD_CHOICES, default='unidad')
    stock_actual    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_minimo    = models.DecimalField(max_digits=10, decimal_places=2, default=5)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proveedor       = models.CharField(max_length=200, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de vencimiento')
    activo          = models.BooleanField(default=True)

    class Meta:
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return self.nombre

    @property
    def necesita_reposicion(self):
        return self.stock_actual <= self.stock_minimo

    @property
    def esta_vencido(self):
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < timezone.now().date()

    @property
    def proxima_expiracion(self):
        """True si vence dentro de los próximos 30 días (sin estar vencido aún)."""
        if not self.fecha_vencimiento:
            return False
        hoy = timezone.now().date()
        return hoy <= self.fecha_vencimiento <= hoy + timedelta(days=30)

    @property
    def dias_para_vencer(self):
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - timezone.now().date()).days


class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('entrada',  'Entrada'),
        ('salida',   'Salida / Uso'),
        ('ajuste',   'Ajuste de inventario'),
        ('vencido',  'Baja por vencimiento'),
    ]

    insumo           = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='movimientos')
    tipo             = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad         = models.DecimalField(max_digits=10, decimal_places=2)
    stock_resultante = models.DecimalField(max_digits=10, decimal_places=2)
    motivo           = models.CharField(max_length=300, blank=True)
    fecha            = models.DateTimeField(auto_now_add=True)
    registrado_por   = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.insumo} - {self.tipo} {self.cantidad}"
