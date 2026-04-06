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
