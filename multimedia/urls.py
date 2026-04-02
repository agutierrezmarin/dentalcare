from django.urls import path
from . import views

app_name = 'multimedia'

urlpatterns = [
    path('paciente/<int:paciente_pk>/', views.galeria_paciente, name='galeria'),
    path('paciente/<int:paciente_pk>/comparar/', views.crear_comparacion, name='comparacion'),
]
