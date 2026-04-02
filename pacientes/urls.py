from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    path('', views.lista_pacientes, name='lista'),
    path('nuevo/', views.crear_paciente, name='crear'),
    path('<int:pk>/', views.detalle_paciente, name='detalle'),
    path('<int:pk>/editar/', views.editar_paciente, name='editar'),
    path('<int:pk>/alergia/', views.agregar_alergia, name='alergia'),
    path('<int:pk>/adjunto/', views.subir_adjunto, name='adjunto'),
]
