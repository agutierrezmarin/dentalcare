from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('buscar/', views.busqueda_global, name='busqueda'),
    path('login/', auth_views.LoginView.as_view(template_name='base/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('pacientes/', include('pacientes.urls')),
    path('agenda/', include('agenda.urls')),
    path('clinico/', include('clinico.urls')),
    path('facturacion/', include('facturacion.urls')),
    path('inventario/', include('inventario.urls')),
    path('personal/', include('personal.urls')),
    path('multimedia/', include('multimedia.urls')),
    path('espacios/', include('espacios.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
