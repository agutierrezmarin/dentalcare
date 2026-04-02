from django.db import models, transaction
from pacientes.models import Paciente
from clinico.models import Tratamiento


class MetodoPago(models.Model):
    nombre = models.CharField(max_length=50)  # Efectivo, QR, Transferencia, etc.
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Pago(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='pagos')
    doctor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    hora = models.TimeField(auto_now_add=True)
    concepto = models.CharField(max_length=300)
    numero_recibo = models.CharField(max_length=50, blank=True)
    notas = models.TextField(blank=True)
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, related_name='pagos_registrados'
    )

    class Meta:
        ordering = ['-fecha', '-hora']

    def __str__(self):
        return f"Pago {self.paciente} - Bs {self.monto} ({self.fecha})"


class PlanPago(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado',    'Pagado'),
        ('vencido',   'Vencido'),
        ('cancelado', 'Cancelado'),
    ]

    tratamiento = models.ForeignKey(Tratamiento, on_delete=models.CASCADE, related_name='plan_pagos')
    numero_cuota = models.IntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente')
    pago = models.ForeignKey(Pago, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_pago = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['tratamiento', 'numero_cuota']

    def __str__(self):
        return f"Cuota {self.numero_cuota} - {self.tratamiento.paciente} - {self.get_estado_display()}"

    @property
    def esta_vencida(self):
        from django.utils import timezone
        return self.estado == 'pendiente' and self.fecha_vencimiento < timezone.now().date()


class Presupuesto(models.Model):
    ESTADO_CHOICES = [
        ('borrador',  'Borrador'),
        ('enviado',   'Enviado'),
        ('aceptado',  'Aceptado'),
        ('rechazado', 'Rechazado'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='presupuestos')
    doctor = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    fecha = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='borrador')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento_global = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    descuento_monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"Presupuesto {self.paciente} - {self.fecha}"


class ItemPresupuesto(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='items')
    servicio = models.ForeignKey('clinico.Servicio', on_delete=models.PROTECT)
    numero_diente = models.IntegerField(null=True, blank=True)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return (self.precio_unitario * self.cantidad) * (1 - self.descuento / 100)


# ── Ticket de cobro ──────────────────────────────────────────────────────────

class Ticket(models.Model):
    ESTADO_CHOICES = [
        ('pagado',  'Pagado'),
        ('anulado', 'Anulado'),
    ]

    numero          = models.CharField(max_length=20, unique=True, editable=False)
    paciente        = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='tickets')
    cita            = models.ForeignKey(
        'agenda.Cita', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets'
    )
    doctor          = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_doctor'
    )
    fecha           = models.DateField(auto_now_add=True)
    hora            = models.TimeField(auto_now_add=True)
    metodo_pago     = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
    descuento_global= models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento_monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado          = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pagado')
    notas           = models.TextField(blank=True)
    registrado_por  = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, related_name='tickets_registrados'
    )

    class Meta:
        ordering = ['-fecha', '-hora']

    def __str__(self):
        return f"Ticket {self.numero} — {self.paciente}"

    def save(self, *args, **kwargs):
        if not self.numero:
            from django.utils import timezone
            año = timezone.now().year
            with transaction.atomic():
                ultimo = (
                    Ticket.objects
                    .select_for_update()
                    .filter(numero__startswith=f'TK-{año}-')
                    .order_by('-numero')
                    .first()
                )
                if ultimo:
                    try:
                        seq = int(ultimo.numero.rsplit('-', 1)[-1]) + 1
                    except (ValueError, IndexError):
                        seq = 1
                else:
                    seq = 1
                self.numero = f'TK-{año}-{seq:04d}'
        super().save(*args, **kwargs)


class ItemTicket(models.Model):
    TIPO_CHOICES = [
        ('servicio', 'Servicio'),
        ('producto', 'Producto'),
    ]

    ticket          = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='items')
    tipo            = models.CharField(max_length=10, choices=TIPO_CHOICES)
    servicio        = models.ForeignKey(
        'clinico.Servicio', on_delete=models.PROTECT, null=True, blank=True
    )
    producto        = models.ForeignKey(
        'inventario.Insumo', on_delete=models.PROTECT, null=True, blank=True
    )
    descripcion     = models.CharField(max_length=300)
    cantidad        = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento       = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    subtotal        = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.descripcion} x{self.cantidad}"
