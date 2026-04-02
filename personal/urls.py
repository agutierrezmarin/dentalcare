from django.urls import path
from . import views

app_name = 'personal'

urlpatterns = [
    path('',                     views.lista_personal,      name='lista'),
    path('nuevo/',               views.crear_personal,      name='crear'),
    path('perfil/',              views.mi_perfil,           name='mi_perfil'),
    path('<int:pk>/editar/',     views.editar_personal,     name='editar'),
    path('<int:pk>/desactivar/', views.desactivar_personal, name='desactivar'),
]
