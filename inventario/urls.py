from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.lista_insumos, name='lista'),
    path('nuevo/', views.crear_insumo, name='crear'),
    path('<int:pk>/movimiento/', views.movimiento, name='movimiento'),
]
