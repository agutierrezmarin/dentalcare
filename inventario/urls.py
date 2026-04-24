from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # Inventario principal
    path('',                          views.lista_insumos,    name='lista'),
    path('nuevo/',                    views.crear_insumo,     name='crear'),
    path('<int:pk>/editar/',          views.editar_insumo,    name='editar'),
    path('<int:pk>/movimiento/',      views.movimiento,       name='movimiento'),
    # Categorías
    path('categorias/',               views.categorias_lista,   name='categorias'),
    path('categorias/nueva/',         views.categoria_crear,    name='categoria_crear'),
    path('categorias/<int:pk>/editar/',   views.categoria_editar,   name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),
]
