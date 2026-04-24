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
    path('citas/disponibilidad/',   views.verificar_disponibilidad, name='disponibilidad'),
    # Espacios
    path('citas/espacio-doctor/', views.espacio_doctor, name='espacio_doctor'),
    # Notificaciones
    path('notificaciones/',              views.notificaciones,       name='notificaciones'),
    path('notificaciones/json/',         views.notificaciones_json,  name='notificaciones_json'),
    path('notificaciones/todas-leidas/', views.marcar_todas_leidas,  name='todas_leidas'),
    path('notificaciones/<int:pk>/leer/', views.marcar_leida,        name='marcar_leida'),
]
