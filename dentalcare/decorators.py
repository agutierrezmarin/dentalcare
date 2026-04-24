from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def solo_admin(view_func):
    """Restringe la vista solo a usuarios con rol 'admin'."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            es_admin = request.user.is_authenticated and request.user.perfil.rol == 'admin'
        except Exception:
            es_admin = False
        if not es_admin:
            messages.warning(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_o_recepcion(view_func):
    """Permite acceso a usuarios con rol 'admin' o 'recepcion'."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            rol = request.user.perfil.rol if request.user.is_authenticated else None
            tiene_acceso = rol in ('admin', 'recepcion')
        except Exception:
            tiene_acceso = False
        if not tiene_acceso:
            messages.warning(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
