from django.db import models
from pacientes.models import Paciente


class FotoClinica(models.Model):
    TIPO_CHOICES = [
        ('antes',       'Antes del tratamiento'),
        ('durante',     'Durante el tratamiento'),
        ('despues',     'Después del tratamiento'),
        ('radiografia', 'Radiografía'),
        ('intraoral',   'Foto intraoral'),
        ('extraoral',   'Foto extraoral'),
        ('panoramica',  'Radiografía panorámica'),
        ('otro',        'Otro'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='fotos_clinicas')
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=200)
    imagen = models.ImageField(upload_to='multimedia/fotos/%Y/%m/')
    descripcion = models.TextField(blank=True)
    fecha = models.DateField(auto_now_add=True)
    subido_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    numero_diente = models.IntegerField(null=True, blank=True)
    tratamiento = models.ForeignKey(
        'clinico.Tratamiento', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='fotos'
    )

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.paciente} - {self.titulo}"


class ComparacionFotos(models.Model):
    """Agrupación antes/después para comparación visual."""
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='comparaciones')
    titulo = models.CharField(max_length=200)
    foto_antes = models.ForeignKey(FotoClinica, on_delete=models.SET_NULL, null=True, related_name='comp_antes')
    foto_despues = models.ForeignKey(FotoClinica, on_delete=models.SET_NULL, null=True, related_name='comp_despues')
    fecha = models.DateField(auto_now_add=True)
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"Comparación {self.paciente} - {self.titulo}"
