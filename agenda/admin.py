from django.contrib import admin
from .models import Cita, Sillon, DisponibilidadDoctor

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'doctor', 'fecha', 'hora_inicio', 'estado']
    list_filter = ['estado', 'fecha']
    search_fields = ['paciente__nombres', 'paciente__apellidos']

admin.site.register(Sillon)
admin.site.register(DisponibilidadDoctor)
