from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import json
from .models import Cita, Sillon, DisponibilidadDoctor, BloqueoAgenda
from .forms import CitaForm, SillonForm, CobrarCitaForm


@login_required
def calendario(request):
    doctores = User.objects.filter(perfil__rol__in=['dentista', 'admin'], perfil__activo=True).select_related('perfil')
    sillones = Sillon.objects.filter(activo=True)
    estados_colores = [
        ('programada',  'Programada',  '#a78bfa'),
        ('confirmada',  'Confirmada',  '#4e9ff5'),
        ('en_curso',    'En curso',    '#34d399'),
        ('completada',  'Completada',  '#6b7280'),
        ('cancelada',   'Cancelada',   '#f87171'),
        ('no_asistio',  'No asistió',  '#f59e0b'),
    ]
    return render(request, 'agenda/calendario.html', {
        'doctores': doctores,
        'sillones': sillones,
        'estados_colores': estados_colores,
    })


@login_required
def citas_json(request):
    """Endpoint JSON para FullCalendar."""
    inicio = request.GET.get('start')
    fin = request.GET.get('end')
    doctor_id = request.GET.get('doctor')

    citas = Cita.objects.select_related(
        'paciente', 'doctor', 'doctor__perfil', 'servicio', 'sillon',
        'tratamiento', 'tratamiento__servicio', 'tratamiento__servicio__categoria'
    ).prefetch_related('tickets')

    if inicio:
        citas = citas.filter(fecha__gte=inicio[:10])
    if fin:
        citas = citas.filter(fecha__lte=fin[:10])
    if doctor_id:
        citas = citas.filter(doctor_id=doctor_id)

    COLOR_COMPLETADA = '#22c55e'
    ESTADO_OPACIDAD  = {'cancelada', 'no_asistio'}

    eventos = []
    for c in citas:
        completada = c.estado == 'completada'

        trat_prefix = '🦷 ' if c.tratamiento_id else ''
        if completada:
            color = COLOR_COMPLETADA
            title = f"✓ {trat_prefix}{c.paciente.apellidos} {c.paciente.nombres[:1]}. — {c.servicio.nombre if c.servicio else ''}"
        else:
            color = '#22d3ee'
            if c.doctor and hasattr(c.doctor, 'perfil'):
                color = c.doctor.perfil.color_agenda or '#22d3ee'
            title = f"{trat_prefix}{c.paciente.apellidos} {c.paciente.nombres[:1]}. — {c.servicio.nombre if c.servicio else ''}"

        eventos.append({
            'id':              c.pk,
            'title':           title,
            'start':           f"{c.fecha}T{c.hora_inicio}",
            'end':             f"{c.fecha}T{c.hora_fin}",
            'backgroundColor': color,
            'borderColor':     color,
            'editable':        not completada,
            'extendedProps': {
                'paciente':       str(c.paciente),
                'paciente_id':    c.paciente.pk,
                'doctor':         c.doctor.get_full_name() if c.doctor else '',
                'doctor_color':   color,
                'sillon':         str(c.sillon) if c.sillon else '',
                'servicio':       c.servicio.nombre if c.servicio else '',
                'estado':         c.estado,
                'estado_display': c.get_estado_display(),
                'motivo':         c.motivo,
                'notas':          c.notas,
                'completada':          completada,
                'opaco':               c.estado in ESTADO_OPACIDAD,
                'ticket_numero':       c.tickets.first().numero if c.tickets.all() else '',
                'ticket_pk':           c.tickets.first().pk    if c.tickets.all() else None,
                'tratamiento_id':      c.tratamiento_id,
                'tratamiento_nombre':  c.tratamiento.servicio.nombre if c.tratamiento else '',
                'tratamiento_cat_color': (
                    c.tratamiento.servicio.categoria.color
                    if c.tratamiento and c.tratamiento.servicio and c.tratamiento.servicio.categoria
                    else ''
                ),
            }
        })
    return JsonResponse(eventos, safe=False)


@login_required
def crear_cita(request):
    from pacientes.forms import PacienteRapidoForm

    if request.method == 'POST':
        es_nuevo = request.POST.get('paciente_nuevo') == '1'

        if es_nuevo:
            paciente_form = PacienteRapidoForm(request.POST)
            cita_form     = CitaForm(request.POST)
            # En modo "nuevo paciente" el campo paciente del formulario
            # no viene seleccionado; lo asignamos manualmente tras crear el paciente.
            cita_form.fields['paciente'].required = False

            p_ok = paciente_form.is_valid()
            c_ok = cita_form.is_valid()

            if p_ok and c_ok:
                paciente      = paciente_form.save()
                cita          = cita_form.save(commit=False)
                cita.paciente = paciente
                cita.save()
                messages.success(request, f'Paciente {paciente} y cita registrados correctamente.')
                return redirect('agenda:calendario')
        else:
            paciente_form = PacienteRapidoForm()
            cita_form     = CitaForm(request.POST)
            if cita_form.is_valid():
                cita = cita_form.save()
                messages.success(request, f'Cita programada para {cita.paciente}.')
                return redirect('agenda:calendario')

    else:
        es_nuevo      = False
        paciente_form = PacienteRapidoForm()
        tratamiento_pk = request.GET.get('tratamiento')
        cita_form     = CitaForm(initial={
            'fecha':        request.GET.get('fecha', date.today()),
            'doctor':       request.GET.get('doctor'),
            'hora_inicio':  request.GET.get('hora_inicio', ''),
            'hora_fin':     request.GET.get('hora_fin', ''),
            'paciente':     request.GET.get('paciente'),
            'servicio':     request.GET.get('servicio'),
            'tratamiento':  tratamiento_pk,
        })

    # Pasar objeto tratamiento al template si viene desde un plan de tratamiento
    tratamiento_obj = None
    tratamiento_pk_get = request.GET.get('tratamiento') or request.POST.get('tratamiento')
    if tratamiento_pk_get:
        from clinico.models import Tratamiento as TratamientoModel
        try:
            tratamiento_obj = TratamientoModel.objects.select_related(
                'servicio', 'servicio__categoria', 'paciente'
            ).get(pk=tratamiento_pk_get)
        except TratamientoModel.DoesNotExist:
            pass

    return render(request, 'agenda/cita_form.html', {
        'form':           cita_form,
        'paciente_form':  paciente_form,
        'titulo':         'Nueva Cita',
        'es_nuevo':       es_nuevo,
        'tratamiento':    tratamiento_obj,
    })


@login_required
def editar_cita(request, pk):
    cita = get_object_or_404(
        Cita.objects.select_related('paciente', 'doctor', 'servicio', 'sillon'), pk=pk
    )
    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cita actualizada.')
            return redirect('agenda:calendario')
    else:
        form = CitaForm(instance=cita)

    ESTADO_COLORES = {
        'programada': '#a78bfa', 'confirmada': '#4e9ff5', 'en_curso': '#f59e0b',
        'completada': '#22c55e', 'cancelada':  '#f87171', 'no_asistio': '#f59e0b',
    }
    estados = [
        (k, v, ESTADO_COLORES.get(k, '#6b7280'))
        for k, v in Cita.ESTADO_CHOICES
    ]
    return render(request, 'agenda/cita_form.html', {
        'form':   form,
        'titulo': 'Editar Cita',
        'cita':   cita,
        'estados': estados,
        'cobrada': cita.tickets.exists(),
    })


@login_required
def cambiar_estado_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
        except (json.JSONDecodeError, ValueError):
            nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Cita.ESTADO_CHOICES):
            cita.estado = nuevo_estado
            cita.save()
    return JsonResponse({'ok': True, 'estado': cita.estado, 'display': cita.get_estado_display()})


@login_required
def mover_cita(request, pk):
    """Drag & drop desde FullCalendar."""
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        data = json.loads(request.body)
        cita.fecha = data['fecha']
        cita.hora_inicio = data['hora_inicio']
        cita.hora_fin = data['hora_fin']
        cita.save()
    return JsonResponse({'ok': True})


@login_required
def citas_hoy(request):
    hoy = date.today()
    citas = Cita.objects.filter(fecha=hoy).select_related(
        'paciente', 'doctor', 'servicio', 'sillon'
    ).order_by('hora_inicio')
    return render(request, 'agenda/hoy.html', {'citas': citas, 'hoy': hoy})


@login_required
def detalle_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    return render(request, 'agenda/detalle_cita.html', {'cita': cita})


@login_required
def cobrar_cita(request, pk):
    from facturacion.models import Pago

    cita = get_object_or_404(Cita, pk=pk)
    paciente = cita.paciente
    deuda = paciente.get_deuda_pendiente()
    historial = paciente.pagos.select_related('metodo_pago').order_by('-fecha', '-hora')[:5]

    precio_base = float(cita.servicio.precio) if cita.servicio else 0.0
    concepto_default = (
        f'Servicio: {cita.servicio.nombre}' if cita.servicio
        else f'Cita del {cita.fecha}'
    )

    if request.method == 'POST':
        form = CobrarCitaForm(request.POST)
        if form.is_valid():
            pago = Pago(
                paciente=paciente,
                doctor=cita.doctor,
                metodo_pago=form.cleaned_data['metodo_pago'],
                monto=form.cleaned_data['monto'],
                fecha=date.today(),
                concepto=form.cleaned_data['concepto'],
                numero_recibo=form.cleaned_data.get('numero_recibo') or '',
                notas=form.cleaned_data.get('notas') or '',
                registrado_por=request.user,
            )
            pago.save()
            messages.success(request, f'Cobro de Bs {pago.monto} registrado para {paciente}.')
            return redirect('agenda:calendario')
    else:
        form = CobrarCitaForm(initial={
            'monto': precio_base,
            'concepto': concepto_default,
            'descuento': 0,
        })

    return render(request, 'agenda/cobrar_cita.html', {
        'form': form,
        'cita': cita,
        'paciente': paciente,
        'deuda': deuda,
        'precio_base': precio_base,
        'historial': historial,
        'titulo': f'Cobrar — {paciente}',
    })
