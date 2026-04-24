def notificaciones_agenda(request):
    """Inyecta conteo y lista de notificaciones en todos los templates."""
    if not request.user.is_authenticated:
        return {}
    from .models import NotificacionAgenda

    base_qs = NotificacionAgenda.objects.filter(destinatario=request.user)

    no_leidas = base_qs.filter(leida=False).count()
    recientes = (
        base_qs
        .select_related('cita', 'cita__paciente', 'cita__doctor')
        .order_by('-creada_en')[:8]
    )

    # Rol del usuario para lógica condicional en templates
    rol = ''
    try:
        rol = request.user.perfil.rol
    except Exception:
        pass

    return {
        'notif_no_leidas': no_leidas,
        'notif_recientes': recientes,
        'usuario_rol': rol,
        'usuario_es_admin': rol == 'admin',
    }
