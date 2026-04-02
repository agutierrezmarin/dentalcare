from django.contrib import admin
from .models import CategoriaServicio, Servicio, Odontograma, EstadoDiente, HistoriaClinica, NotaClinica, Tratamiento


admin.site.register(CategoriaServicio)

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'duracion_minutos', 'activo']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre']


@admin.register(Tratamiento)
class TratamientoAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'servicio', 'doctor', 'estado', 'precio_acordado']
    list_filter = ['estado']
    search_fields = ['paciente__nombres', 'paciente__apellidos']


admin.site.register(Odontograma)
admin.site.register(EstadoDiente)
admin.site.register(HistoriaClinica)
admin.site.register(NotaClinica)
