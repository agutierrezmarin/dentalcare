from django.utils import timezone
from datetime import timedelta


def alertas_inventario(request):
    """Inyecta contadores de alertas de inventario en todos los templates."""
    if not request.user.is_authenticated:
        return {}
    try:
        rol = request.user.perfil.rol
    except Exception:
        return {}
    if rol not in ('admin', 'recepcion'):
        return {}

    from .models import Insumo
    hoy = timezone.now().date()
    limite = hoy + timedelta(days=30)

    insumos_activos = Insumo.objects.filter(activo=True)
    vencidos = insumos_activos.filter(fecha_vencimiento__lt=hoy).count()
    por_vencer = insumos_activos.filter(
        fecha_vencimiento__gte=hoy,
        fecha_vencimiento__lte=limite,
    ).count()
    total_alertas_vencimiento = vencidos + por_vencer

    return {
        'inv_vencidos': vencidos,
        'inv_por_vencer': por_vencer,
        'inv_total_alertas': total_alertas_vencimiento,
    }
