from django.urls import path
from . import views

app_name = 'agenda'

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('hoy/', views.citas_hoy, name='hoy'),
    path('citas/json/', views.citas_json, name='citas_json'),
    path('citas/nueva/', views.crear_cita, name='crear_cita'),
    path('citas/<int:pk>/', views.detalle_cita, name='detalle_cita'),
    path('citas/<int:pk>/editar/', views.editar_cita, name='editar_cita'),
    path('citas/<int:pk>/estado/', views.cambiar_estado_cita, name='estado_cita'),
    path('citas/<int:pk>/mover/',   views.mover_cita,   name='mover_cita'),
    path('citas/<int:pk>/cobrar/',  views.cobrar_cita,  name='cobrar_cita'),
]
