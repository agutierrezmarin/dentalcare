from django.urls import path
from . import views

app_name = 'multimedia'

urlpatterns = [
    path('paciente/<int:paciente_pk>/', views.galeria_paciente, name='galeria'),
    path('paciente/<int:paciente_pk>/comparar/', views.crear_comparacion, name='comparacion'),
    path('foto/<int:foto_pk>/eliminar/', views.eliminar_foto, name='eliminar_foto'),
    path('comparacion/<int:comp_pk>/eliminar/', views.eliminar_comparacion, name='eliminar_comparacion'),
]
