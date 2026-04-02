from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from datetime import date


@login_required
def dashboard(request):
    from pacientes.models import Paciente
    from agenda.models import Cita
    from facturacion.models import Pago

    hoy = date.today()
    inicio_mes = hoy.replace(day=1)

    citas_hoy = Cita.objects.filter(fecha=hoy).select_related('paciente', 'doctor', 'servicio')
    total_pacientes = Paciente.objects.filter(activo=True).count()
    citas_mes = Cita.objects.filter(fecha__gte=inicio_mes).count()
    ingresos_mes = Pago.objects.filter(
        fecha__gte=inicio_mes
    ).aggregate(total=Sum('monto'))['total'] or 0

    proximas_citas = Cita.objects.filter(
        fecha__gte=hoy,
        estado__in=['programada', 'confirmada']
    ).order_by('fecha', 'hora_inicio').select_related('paciente', 'servicio')[:5]

    return render(request, 'base/dashboard.html', {
        'citas_hoy': citas_hoy,
        'total_pacientes': total_pacientes,
        'citas_mes': citas_mes,
        'ingresos_mes': ingresos_mes,
        'proximas_citas': proximas_citas,
        'hoy': hoy,
    })


@login_required
def busqueda_global(request):
    from pacientes.models import Paciente
    from django.db.models import Q
    q = request.GET.get('q', '').strip()
    resultados = []
    if len(q) >= 2:
        pacientes = Paciente.objects.filter(
            Q(nombres__icontains=q) | Q(apellidos__icontains=q) |
            Q(ci__icontains=q) | Q(telefono__icontains=q),
            activo=True
        )[:8]
        for p in pacientes:
            resultados.append({
                'id': p.pk,
                'texto': f"{p.apellidos} {p.nombres}",
                'subtexto': f"CI: {p.ci or '—'} | Tel: {p.telefono or '—'}",
                'url': f"/pacientes/{p.pk}/",
            })
    return JsonResponse({'resultados': resultados})
