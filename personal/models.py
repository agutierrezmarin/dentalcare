from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    ROL_CHOICES = [
        ('admin',     'Administrador'),
        ('dentista',  'Dentista'),
        ('asistente', 'Asistente'),
        ('recepcion', 'Recepcionista'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=15, choices=ROL_CHOICES, default='asistente')
    telefono = models.CharField(max_length=20, blank=True)
    especialidad = models.CharField(max_length=100, blank=True)  # Para dentistas
    foto = models.ImageField(upload_to='personal/fotos/', null=True, blank=True)
    color_agenda = models.CharField(max_length=7, default='#22d3ee')
    activo = models.BooleanField(default=True)
    firma_digital = models.ImageField(upload_to='personal/firmas/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_rol_display()})"

    @property
    def es_dentista(self):
        return self.rol == 'dentista'

    @property
    def es_admin(self):
        return self.rol == 'admin'
