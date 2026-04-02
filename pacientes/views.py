from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Paciente, Alergia, AdjuntoPaciente
from .forms import PacienteForm, AlergiaForm, AdjuntoForm


@login_required
def lista_pacientes(request):
    from agenda.models import Cita
    from facturacion.models import Pago

    q   = request.GET.get('q', '')
    hoy = timezone.now().date()

    qs = Paciente.objects.filter(activo=True).order_by('apellidos', 'nombres')
    if q:
        qs = qs.filter(
            Q(nombres__icontains=q) | Q(apellidos__icontains=q) |
            Q(ci__icontains=q)      | Q(telefono__icontains=q)
        )

    ids = list(qs.values_list('pk', flat=True))

    # ── Próximas citas (primera por paciente) ────────────────────────────
    proximas_map = {}
    for cita in (Cita.objects
                 .filter(paciente_id__in=ids, fecha__gte=hoy,
                         estado__in=['programada', 'confirmada', 'en_curso'])
                 .select_related('doctor', 'servicio', 'doctor__perfil')
                 .order_by('fecha', 'hora_inicio')):
        proximas_map.setdefault(cita.paciente_id, cita)

    # ── Última cita completada (primera por paciente en orden desc) ──────
    ultimas_map = {}
    for cita in (Cita.objects
                 .filter(paciente_id__in=ids, estado='completada')
                 .select_related('doctor', 'servicio')
                 .order_by('-fecha', '-hora_inicio')):
        ultimas_map.setdefault(cita.paciente_id, cita)

    # ── Total pagado por paciente ────────────────────────────────────────
    pagos_map = dict(
        Pago.objects.filter(paciente_id__in=ids)
        .values('paciente_id')
        .annotate(total=Sum('monto'))
        .values_list('paciente_id', 'total')
    )

    # ── Armar lista enriquecida ──────────────────────────────────────────
    ESTADO_CITA = {
        'programada': ('Programado',  '#4e9ff5'),
        'confirmada': ('Confirmado',  '#a78bfa'),
        'en_curso':   ('En atención', '#f59e0b'),
    }
    enriched = []
    for p in qs:
        proxima = proximas_map.get(p.pk)
        ultima  = ultimas_map.get(p.pk)
        total_pagado = pagos_map.get(p.pk, 0)
        deuda = p.get_deuda_pendiente()

        if proxima:
            lbl, col = ESTADO_CITA.get(proxima.estado, ('Programado', '#4e9ff5'))
            if proxima.fecha == hoy:
                lbl = 'Cita hoy'
                col = '#34d399'
            estado = (lbl, col)
        elif ultima:
            estado = ('Atendido', '#6b7280')
        else:
            estado = ('Sin cita', '#94a3b8')

        enriched.append({
            'p':            p,
            'deuda':        deuda,
            'proxima':      proxima,
            'ultima':       ultima,
            'total_pagado': total_pagado,
            'estado_label': estado[0],
            'estado_color': estado[1],
        })

    return render(request, 'pacientes/lista.html', {
        'enriched': enriched,
        'q':        q,
        'total':    len(enriched),
    })


@login_required
def detalle_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    from clinico.models import Tratamiento, HistoriaClinica, Odontograma
    from agenda.models import Cita
    from facturacion.models import PlanPago

    tratamientos = (
        Tratamiento.objects.filter(paciente=paciente)
        .select_related('servicio', 'servicio__categoria', 'doctor')
        .prefetch_related('citas')
    )
    citas = Cita.objects.filter(paciente=paciente).order_by('-fecha')[:10]
    cuotas_pendientes = PlanPago.objects.filter(
        tratamiento__paciente=paciente, estado='pendiente'
    ).order_by('fecha_vencimiento')
    odontogramas = Odontograma.objects.filter(paciente=paciente)
    adjuntos = AdjuntoPaciente.objects.filter(paciente=paciente)

    try:
        historia = paciente.historia
    except Exception:
        historia = None

    context = {
        'paciente':          paciente,
        'tratamientos':      tratamientos,
        'citas':             citas,
        'cuotas_pendientes': cuotas_pendientes,
        'odontogramas':      odontogramas,
        'adjuntos':          adjuntos,
        'historia':          historia,
        'alergia_form':      AlergiaForm(),
        'adjunto_form':      AdjuntoForm(),
    }
    return render(request, 'pacientes/detalle.html', context)


@login_required
def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST, request.FILES)
        if form.is_valid():
            paciente = form.save()
            from clinico.models import HistoriaClinica
            HistoriaClinica.objects.create(paciente=paciente)
            messages.success(request, f'Paciente {paciente.nombre_completo} registrado correctamente.')
            return redirect('pacientes:detalle', pk=paciente.pk)
    else:
        form = PacienteForm()
    return render(request, 'pacientes/form.html', {'form': form, 'titulo': 'Nuevo Paciente'})


@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        form = PacienteForm(request.POST, request.FILES, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente actualizado.')
            return redirect('pacientes:detalle', pk=pk)
    else:
        form = PacienteForm(instance=paciente)
    return render(request, 'pacientes/form.html', {'form': form, 'titulo': 'Editar Paciente', 'paciente': paciente})


@login_required
def agregar_alergia(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        form = AlergiaForm(request.POST)
        if form.is_valid():
            alergia = form.save(commit=False)
            alergia.paciente = paciente
            alergia.save()
            messages.success(request, 'Alergia registrada.')
    return redirect('pacientes:detalle', pk=pk)


@login_required
def subir_adjunto(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    if request.method == 'POST':
        form = AdjuntoForm(request.POST, request.FILES)
        if form.is_valid():
            adjunto = form.save(commit=False)
            adjunto.paciente = paciente
            adjunto.subido_por = request.user
            adjunto.save()
            messages.success(request, 'Archivo adjuntado correctamente.')
    return redirect('pacientes:detalle', pk=pk)
