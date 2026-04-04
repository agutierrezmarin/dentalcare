from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import json

from .models import Pago, PlanPago, MetodoPago, Presupuesto, ItemPresupuesto, Ticket, ItemTicket
from .forms import PagoForm, PlanPagoForm, PresupuestoForm
from pacientes.models import Paciente
from clinico.models import Tratamiento


@login_required
def registrar_pago(request, paciente_pk=None):
    paciente = None
    if paciente_pk:
        paciente = get_object_or_404(Paciente, pk=paciente_pk)

    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            pago = form.save(commit=False)
            pago.registrado_por = request.user
            pago.save()

            cuota_id = request.POST.get('cuota_id')
            if cuota_id:
                try:
                    cuota = PlanPago.objects.get(pk=cuota_id)
                    cuota.estado = 'pagado'
                    cuota.pago = pago
                    cuota.fecha_pago = pago.fecha
                    cuota.save()
                except PlanPago.DoesNotExist:
                    pass

            messages.success(request, f'Pago de Bs {pago.monto} registrado correctamente.')
            return redirect('facturacion:detalle_pagos', paciente_pk=pago.paciente.pk)
    else:
        initial = {'paciente': paciente, 'fecha': date.today()}
        form = PagoForm(initial=initial)

    return render(request, 'facturacion/pago_form.html', {
        'form': form, 'paciente': paciente
    })


@login_required
def detalle_pagos(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    pagos = Pago.objects.filter(paciente=paciente).order_by('-fecha')
    planes = PlanPago.objects.filter(
        tratamiento__paciente=paciente
    ).select_related('tratamiento__servicio').order_by('fecha_vencimiento')

    total_pagado = pagos.aggregate(t=Sum('monto'))['t'] or 0
    deuda_pendiente = planes.filter(estado='pendiente').aggregate(t=Sum('monto'))['t'] or 0

    return render(request, 'facturacion/detalle_pagos.html', {
        'paciente': paciente,
        'pagos': pagos,
        'planes': planes,
        'total_pagado': total_pagado,
        'deuda_pendiente': deuda_pendiente,
    })


@login_required
def crear_plan_pago(request, tratamiento_pk):
    tratamiento = get_object_or_404(Tratamiento, pk=tratamiento_pk)
    if request.method == 'POST':
        cuotas = int(request.POST.get('cuotas', 1))
        fecha_primera = request.POST.get('fecha_primera')
        from datetime import datetime, timedelta
        fecha = datetime.strptime(fecha_primera, '%Y-%m-%d').date()
        monto_cuota = tratamiento.precio_acordado / cuotas

        for i in range(1, cuotas + 1):
            PlanPago.objects.create(
                tratamiento=tratamiento,
                numero_cuota=i,
                monto=round(monto_cuota, 2),
                fecha_vencimiento=fecha,
            )
            fecha = fecha + timedelta(days=30)

        messages.success(request, f'Plan de {cuotas} cuota(s) creado.')
    return redirect('facturacion:detalle_pagos', paciente_pk=tratamiento.paciente.pk)


@login_required
def reporte_ingresos(request):
    from dateutil.relativedelta import relativedelta
    hoy = date.today()
    inicio_mes  = hoy.replace(day=1)
    inicio_anio = hoy.replace(month=1, day=1)

    # ── Pagos del mes ──────────────────────────────
    pagos_mes   = Pago.objects.filter(fecha__gte=inicio_mes).select_related('paciente', 'metodo_pago', 'doctor')
    total_mes   = pagos_mes.aggregate(t=Sum('monto'))['t'] or 0
    total_anio  = Pago.objects.filter(fecha__gte=inicio_anio).aggregate(t=Sum('monto'))['t'] or 0
    pacientes_mes = pagos_mes.values('paciente').distinct().count()

    # ── Por método de pago (mes) ───────────────────
    por_metodo = (
        Pago.objects.filter(fecha__gte=inicio_mes)
        .values('metodo_pago__nombre')
        .annotate(total=Sum('monto'), cantidad=Count('id'))
        .order_by('-total')
    )

    # ── Deudas pendientes ──────────────────────────
    deudas = PlanPago.objects.filter(estado='pendiente').select_related(
        'tratamiento__paciente', 'tratamiento__servicio'
    ).order_by('fecha_vencimiento')
    total_deudas = deudas.aggregate(t=Sum('monto'))['t'] or 0

    # ── Por dentista (mes actual) ──────────────────
    por_doctor = (
        Pago.objects.filter(fecha__gte=inicio_mes)
        .values('doctor__id', 'doctor__first_name', 'doctor__last_name', 'doctor__username')
        .annotate(total=Sum('monto'), cantidad=Count('id'), pacientes=Count('paciente', distinct=True))
        .order_by('-total')
    )

    # ── Gráfico: últimos 30 días ───────────────────
    dias_data = []
    for i in range(29, -1, -1):
        dia   = hoy - timedelta(days=i)
        total = Pago.objects.filter(fecha=dia).aggregate(t=Sum('monto'))['t'] or 0
        dias_data.append({'periodo': dia.strftime('%d/%m'), 'total': float(total)})

    # ── Gráfico: últimos 12 meses ──────────────────
    meses_data = []
    for i in range(11, -1, -1):
        ms  = hoy.replace(day=1) - relativedelta(months=i)
        mf  = ms + relativedelta(months=1)
        total = Pago.objects.filter(fecha__gte=ms, fecha__lt=mf).aggregate(t=Sum('monto'))['t'] or 0
        meses_data.append({'periodo': ms.strftime('%b %Y'), 'total': float(total)})

    # ── Gráfico: últimos 5 años ────────────────────
    anios_data = []
    for i in range(4, -1, -1):
        anio  = hoy.year - i
        total = Pago.objects.filter(fecha__year=anio).aggregate(t=Sum('monto'))['t'] or 0
        anios_data.append({'periodo': str(anio), 'total': float(total)})

    return render(request, 'facturacion/reporte.html', {
        'pagos_mes':     pagos_mes,
        'total_mes':     total_mes,
        'total_anio':    total_anio,
        'pacientes_mes': pacientes_mes,
        'por_metodo':    por_metodo,
        'deudas':        deudas,
        'total_deudas':  total_deudas,
        'por_doctor':    por_doctor,
        'dias_data':     json.dumps(dias_data),
        'meses_data':    json.dumps(meses_data),
        'anios_data':    json.dumps(anios_data),
        'hoy':           hoy,
    })


@login_required
def crear_presupuesto(request, paciente_pk):
    from clinico.models import Servicio
    paciente = get_object_or_404(Paciente, pk=paciente_pk)

    if request.method == 'POST':
        form = PresupuestoForm(request.POST)
        items_json_str   = request.POST.get('items_json', '[]')
        descuento_global = Decimal(request.POST.get('descuento_global', '0') or '0')
        try:
            items_data = json.loads(items_json_str)
        except json.JSONDecodeError:
            items_data = []

        if not items_data:
            messages.error(request, 'Agrega al menos un servicio al presupuesto.')
        elif form.is_valid():
            # Calcular montos
            subtotal = Decimal('0')
            for item in items_data:
                cant   = Decimal(str(item.get('cantidad', 1)))
                precio = Decimal(str(item.get('precio_unitario', 0)))
                desc   = Decimal(str(item.get('descuento', 0)))
                subtotal += cant * precio * (1 - desc / 100)

            descuento_monto = subtotal * descuento_global / 100
            total           = subtotal - descuento_monto

            p = form.save(commit=False)
            p.paciente        = paciente
            p.doctor          = request.user
            p.subtotal        = subtotal
            p.descuento_global = descuento_global
            p.descuento_monto = descuento_monto
            p.total           = total
            p.save()

            for item in items_data:
                ref_id = item.get('ref_id')
                try:
                    servicio_obj = Servicio.objects.get(pk=ref_id) if ref_id else None
                except Servicio.DoesNotExist:
                    servicio_obj = None
                if servicio_obj:
                    ItemPresupuesto.objects.create(
                        presupuesto    = p,
                        servicio       = servicio_obj,
                        numero_diente  = item.get('numero_diente') or None,
                        cantidad       = int(Decimal(str(item.get('cantidad', 1)))),
                        precio_unitario= Decimal(str(item.get('precio_unitario', 0))),
                        descuento      = Decimal(str(item.get('descuento', 0))),
                    )

            messages.success(request, f'Presupuesto #{p.pk} creado correctamente.')
            return redirect('facturacion:ver_presupuesto', pk=p.pk)

    else:
        form = PresupuestoForm()

    servicios = (
        Servicio.objects.filter(activo=True)
        .select_related('categoria')
        .order_by('categoria__nombre', 'nombre')
    )
    servicios_json = json.dumps([{
        'pk':      s.pk,
        'nombre':  s.nombre,
        'precio':  float(s.precio),
        'duracion': s.duracion_minutos,
        'cat':     s.categoria.nombre if s.categoria else '',
        'color':   s.categoria.color  if s.categoria else '#6b7280',
        'desc':    s.descripcion[:80] if s.descripcion else '',
    } for s in servicios])

    return render(request, 'facturacion/presupuesto_form.html', {
        'form':          form,
        'paciente':      paciente,
        'servicios':     servicios,
        'servicios_json': servicios_json,
    })


@login_required
def ver_presupuesto(request, pk):
    presupuesto = get_object_or_404(Presupuesto, pk=pk)
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion in ('enviado', 'aceptado', 'rechazado'):
            presupuesto.estado = accion
            presupuesto.save()
            messages.success(request, f'Presupuesto marcado como {accion}.')
    return render(request, 'facturacion/presupuesto_ver.html', {'presupuesto': presupuesto})


# ── Tickets ──────────────────────────────────────────────────────────────────

@login_required
def crear_ticket(request, cita_pk):
    from agenda.models import Cita
    from inventario.models import Insumo, MovimientoInventario
    from clinico.models import Servicio

    cita     = get_object_or_404(Cita, pk=cita_pk)
    paciente = cita.paciente
    deuda    = paciente.get_deuda_pendiente()

    if request.method == 'POST':
        metodo_pago_id   = request.POST.get('metodo_pago')
        descuento_global = Decimal(request.POST.get('descuento_global', '0') or '0')
        notas            = request.POST.get('notas', '')
        items_json_str   = request.POST.get('items_json', '[]')

        try:
            items_data = json.loads(items_json_str)
        except json.JSONDecodeError:
            items_data = []

        error = None
        if not items_data:
            error = 'Agrega al menos un ítem al ticket.'
        elif not metodo_pago_id:
            error = 'Selecciona un método de pago.'

        if error:
            messages.error(request, error)
        else:
            metodo_pago = get_object_or_404(MetodoPago, pk=metodo_pago_id)

            subtotal = Decimal('0')
            for item in items_data:
                cant   = Decimal(str(item.get('cantidad', 1)))
                precio = Decimal(str(item.get('precio_unitario', 0)))
                desc   = Decimal(str(item.get('descuento', 0)))
                subtotal += cant * precio * (1 - desc / 100)

            descuento_monto = subtotal * descuento_global / 100
            total           = subtotal - descuento_monto

            ticket = Ticket(
                paciente=paciente,
                cita=cita,
                doctor=cita.doctor,
                metodo_pago=metodo_pago,
                descuento_global=descuento_global,
                subtotal=subtotal,
                descuento_monto=descuento_monto,
                total=total,
                estado='pagado',
                notas=notas,
                registrado_por=request.user,
            )
            ticket.save()

            for item in items_data:
                cant          = Decimal(str(item.get('cantidad', 1)))
                precio        = Decimal(str(item.get('precio_unitario', 0)))
                desc          = Decimal(str(item.get('descuento', 0)))
                item_subtotal = cant * precio * (1 - desc / 100)
                tipo          = item.get('tipo', 'servicio')
                servicio_obj  = None
                producto_obj  = None

                if tipo == 'servicio' and item.get('ref_id'):
                    try:
                        servicio_obj = Servicio.objects.get(pk=item['ref_id'])
                    except Servicio.DoesNotExist:
                        pass
                elif tipo == 'producto' and item.get('ref_id'):
                    try:
                        producto_obj  = Insumo.objects.get(pk=item['ref_id'])
                        nuevo_stock   = max(Decimal('0'), producto_obj.stock_actual - cant)
                        producto_obj.stock_actual = nuevo_stock
                        producto_obj.save(update_fields=['stock_actual'])
                        MovimientoInventario.objects.create(
                            insumo=producto_obj,
                            tipo='salida',
                            cantidad=cant,
                            stock_resultante=nuevo_stock,
                            motivo=f'Venta — Ticket {ticket.numero}',
                            registrado_por=request.user,
                        )
                    except Insumo.DoesNotExist:
                        pass

                ItemTicket.objects.create(
                    ticket=ticket,
                    tipo=tipo,
                    servicio=servicio_obj,
                    producto=producto_obj,
                    descripcion=item.get('descripcion', ''),
                    cantidad=cant,
                    precio_unitario=precio,
                    descuento=desc,
                    subtotal=item_subtotal,
                )

            # Registro en Pago para compatibilidad con reportes existentes
            Pago.objects.create(
                paciente=paciente,
                doctor=cita.doctor,
                metodo_pago=metodo_pago,
                monto=total,
                fecha=date.today(),
                concepto=f'Ticket {ticket.numero}',
                registrado_por=request.user,
            )

            # Marcar la cita como completada automáticamente
            if cita.estado not in ('cancelada', 'no_asistio'):
                cita.estado = 'completada'
                cita.save(update_fields=['estado'])

            messages.success(request, f'Ticket {ticket.numero} registrado — Bs {total}.')
            return redirect('facturacion:ticket_detalle', pk=ticket.pk)

    # GET — preparar contexto
    from clinico.models import Servicio
    from inventario.models import Insumo

    servicios = Servicio.objects.filter(activo=True).select_related('categoria').order_by('categoria__nombre', 'nombre')
    productos  = Insumo.objects.filter(activo=True, stock_actual__gt=0).order_by('nombre')
    metodos    = MetodoPago.objects.filter(activo=True)

    items_iniciales = []
    if cita.servicio:
        items_iniciales.append({
            'tipo': 'servicio',
            'ref_id': cita.servicio.pk,
            'descripcion': cita.servicio.nombre,
            'cantidad': 1,
            'precio_unitario': float(cita.servicio.precio),
            'descuento': 0,
        })

    return render(request, 'facturacion/ticket_form.html', {
        'cita':               cita,
        'paciente':           paciente,
        'deuda':              deuda,
        'servicios':          servicios,
        'productos':          productos,
        'metodos':            metodos,
        'items_iniciales_json': json.dumps(items_iniciales),
        'titulo':             f'Nuevo Ticket — {paciente}',
    })


@login_required
def ticket_detalle(request, pk):
    from agenda.models import Cita

    ticket   = get_object_or_404(
        Ticket.objects
        .select_related('paciente', 'doctor', 'metodo_pago', 'cita', 'registrado_por')
        .prefetch_related('items__servicio', 'items__producto'),
        pk=pk,
    )
    paciente = ticket.paciente
    hoy      = timezone.now().date()

    proxima_cita = (
        Cita.objects
        .filter(paciente=paciente, fecha__gte=hoy, estado__in=['programada', 'confirmada'])
        .select_related('servicio', 'doctor')
        .order_by('fecha', 'hora_inicio')
        .first()
    )
    historial_citas = (
        Cita.objects
        .filter(paciente=paciente)
        .select_related('servicio', 'doctor')
        .order_by('-fecha', '-hora_inicio')[:8]
    )
    deuda           = paciente.get_deuda_pendiente()
    tickets_recientes = (
        Ticket.objects
        .filter(paciente=paciente)
        .select_related('metodo_pago')
        .order_by('-fecha', '-hora')[:6]
    )

    return render(request, 'facturacion/ticket_detalle.html', {
        'ticket':           ticket,
        'paciente':         paciente,
        'proxima_cita':     proxima_cita,
        'historial_citas':  historial_citas,
        'deuda':            deuda,
        'tickets_recientes': tickets_recientes,
    })


@login_required
def buscar_items_ticket(request):
    from clinico.models import Servicio
    from inventario.models import Insumo

    q       = request.GET.get('q', '').strip()
    results = []

    if q:
        for s in Servicio.objects.filter(nombre__icontains=q, activo=True)[:6]:
            results.append({
                'tipo':            'servicio',
                'ref_id':          s.pk,
                'descripcion':     s.nombre,
                'precio_unitario': float(s.precio),
                'unidad':          'sesión',
                'extra':           str(s.categoria) if s.categoria else '',
            })
        for p in Insumo.objects.filter(nombre__icontains=q, activo=True, stock_actual__gt=0)[:6]:
            results.append({
                'tipo':            'producto',
                'ref_id':          p.pk,
                'descripcion':     p.nombre,
                'precio_unitario': float(p.precio_unitario),
                'unidad':          p.get_unidad_display(),
                'extra':           f'Stock: {p.stock_actual}',
            })

    return JsonResponse({'results': results})
