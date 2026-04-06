from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import JsonResponse
from datetime import date


@login_required
def dashboard(request):
    from pacientes.models import Paciente
    from agenda.models import Cita
    from facturacion.models import Pago

    hoy        = date.today()
    inicio_mes = hoy.replace(day=1)
    es_admin   = hasattr(request.user, 'perfil') and request.user.perfil.rol == 'admin'

    ESTADOS_LABEL = {
        'programada': ('Programadas', '#a78bfa'),
        'confirmada':  ('Confirmadas',  '#4e9ff5'),
        'en_curso':    ('En curso',     '#f59e0b'),
        'completada':  ('Completadas',  '#22c55e'),
        'cancelada':   ('Canceladas',   '#f87171'),
        'no_asistio':  ('No asistió',   '#94a3b8'),
    }

    if es_admin:
        citas_hoy = (Cita.objects
                     .filter(fecha=hoy)
                     .select_related('paciente', 'doctor', 'servicio')
                     .order_by('hora_inicio'))

        total_pacientes = Paciente.objects.filter(activo=True).count()
        citas_mes       = Cita.objects.filter(fecha__gte=inicio_mes).count()
        citas_completadas_mes = None
        ingresos_mes    = (Pago.objects
                           .filter(fecha__gte=inicio_mes)
                           .aggregate(total=Sum('monto'))['total'] or 0)

        proximas_citas = (Cita.objects
                          .filter(fecha__gte=hoy, estado__in=['programada', 'confirmada'])
                          .order_by('fecha', 'hora_inicio')
                          .select_related('paciente', 'doctor', 'servicio')[:8])

        raw = (Cita.objects.filter(fecha=hoy)
               .values('estado').annotate(total=Count('id')))
        resumen_estados = [
            {'label': ESTADOS_LABEL[r['estado']][0],
             'color': ESTADOS_LABEL[r['estado']][1],
             'total': r['total']}
            for r in raw if r['estado'] in ESTADOS_LABEL
        ]

    else:
        citas_hoy = (Cita.objects
                     .filter(fecha=hoy, doctor=request.user)
                     .select_related('paciente', 'doctor', 'servicio')
                     .order_by('hora_inicio'))

        total_pacientes = (Cita.objects
                           .filter(doctor=request.user)
                           .values('paciente').distinct().count())

        citas_mes = Cita.objects.filter(
            fecha__gte=inicio_mes, doctor=request.user
        ).count()

        citas_completadas_mes = Cita.objects.filter(
            fecha__gte=inicio_mes, doctor=request.user, estado='completada'
        ).count()

        ingresos_mes = None
        resumen_estados = []

        proximas_citas = (Cita.objects
                          .filter(fecha__gte=hoy, doctor=request.user,
                                  estado__in=['programada', 'confirmada'])
                          .order_by('fecha', 'hora_inicio')
                          .select_related('paciente', 'servicio')[:8])

    return render(request, 'base/dashboard.html', {
        'citas_hoy':             citas_hoy,
        'total_pacientes':       total_pacientes,
        'citas_mes':             citas_mes,
        'citas_completadas_mes': citas_completadas_mes,
        'ingresos_mes':          ingresos_mes,
        'proximas_citas':        proximas_citas,
        'resumen_estados':       resumen_estados,
        'hoy':                   hoy,
        'es_admin':              es_admin,
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
