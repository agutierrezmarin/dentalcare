from django.urls import path
from . import views

app_name = 'espacios'

urlpatterns = [
    path('',                           views.lista_espacios,          name='lista'),
    path('nuevo/',                     views.crear_espacio,           name='crear'),
    path('<int:pk>/',                  views.detalle_espacio,         name='detalle'),
    path('<int:pk>/editar/',           views.editar_espacio,          name='editar'),
    path('<int:pk>/eliminar/',         views.eliminar_espacio,        name='eliminar'),
    path('<int:pk>/estado/',           views.cambiar_estado,          name='estado'),
    path('<int:pk>/mantenimiento/',    views.registrar_mantenimiento, name='mantenimiento'),
]
