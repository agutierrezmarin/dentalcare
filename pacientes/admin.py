from django.contrib import admin
from .models import Paciente, Alergia, AdjuntoPaciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['apellidos', 'nombres', 'ci', 'telefono', 'activo', 'fecha_registro']
    list_filter = ['activo', 'sexo', 'tipo_sangre']
    search_fields = ['nombres', 'apellidos', 'ci', 'telefono']
    date_hierarchy = 'fecha_registro'


@admin.register(Alergia)
class AlergiaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'tipo', 'descripcion', 'gravedad']
    list_filter = ['tipo', 'gravedad']


admin.site.register(AdjuntoPaciente)
