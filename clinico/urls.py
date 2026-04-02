from django.urls import path
from . import views

app_name = 'clinico'

urlpatterns = [
    path('paciente/<int:paciente_pk>/odontograma/', views.odontograma, name='odontograma'),
    path('paciente/<int:paciente_pk>/odontograma/guardar/', views.guardar_odontograma, name='guardar_odontograma'),
    path('paciente/<int:paciente_pk>/historia/', views.historia_clinica, name='historia'),
    path('paciente/<int:paciente_pk>/tratamientos/', views.lista_tratamientos, name='tratamientos'),
    path('tratamiento/<int:pk>/estado/', views.actualizar_estado_tratamiento, name='estado_tratamiento'),
    path('servicios/', views.lista_servicios, name='servicios'),
    path('servicios/<int:pk>/editar/', views.editar_servicio, name='editar_servicio'),
    path('servicios/<int:pk>/toggle/', views.toggle_servicio, name='toggle_servicio'),
]
