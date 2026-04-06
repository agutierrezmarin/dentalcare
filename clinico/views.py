from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from dentalcare.decorators import solo_admin
from pacientes.models import Paciente
from .models import (
    Odontograma, EstadoDiente, HistoriaClinica,
    NotaClinica, Tratamiento, Servicio, CategoriaServicio
)
from .forms import TratamientoForm, NotaClinicaForm, ServicioForm


@login_required
def odontograma(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    odontogramas = Odontograma.objects.filter(paciente=paciente).prefetch_related('estados').order_by('-fecha', '-pk')

    # Último odontograma (más reciente por fecha y pk)
    odontograma_actual = odontogramas.first()
    estados = {}
    if odontograma_actual:
        for e in odontograma_actual.estados.all():
            key = f"{e.numero_diente}_{e.cara}"
            estados[key] = {
                'condicion': e.condicion,
                'color': e.color_hex,
                'notas': e.notas,
            }

    return render(request, 'clinico/odontograma.html', {
        'paciente': paciente,
        'odontograma_actual': odontograma_actual,
        'estados_json': json.dumps(estados),
        'odontogramas': odontogramas,
    })


@login_required
def guardar_odontograma(request, paciente_pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    from django.utils import timezone

    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    data = json.loads(request.body)
    hoy = timezone.localdate()

    # Si ya existe un odontograma de hoy, actualizar; si no, crear uno nuevo
    odontograma_obj = (
        Odontograma.objects
        .filter(paciente=paciente, fecha=hoy)
        .order_by('-pk')
        .first()
    )
    if odontograma_obj:
        # Borrar estados anteriores y reemplazar
        odontograma_obj.estados.all().delete()
        odontograma_obj.notas = data.get('notas', '')
        odontograma_obj.save()
    else:
        odontograma_obj = Odontograma.objects.create(
            paciente=paciente,
            creado_por=request.user,
            notas=data.get('notas', '')
        )

    EstadoDiente.objects.bulk_create([
        EstadoDiente(
            odontograma=odontograma_obj,
            numero_diente=item['diente'],
            condicion=item['condicion'],
            cara=item.get('cara', 'general'),
            notas=item.get('notas', ''),
            color_hex=item.get('color', '#22d3ee'),
        )
        for item in data.get('estados', [])
    ])

    return JsonResponse({'success': True, 'id': odontograma_obj.pk})


@login_required
def historia_clinica(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    historia, _ = HistoriaClinica.objects.get_or_create(paciente=paciente)
    notas = historia.notas.all().select_related('doctor')

    if request.method == 'POST':
        form = NotaClinicaForm(request.POST)
        if form.is_valid():
            nota = form.save(commit=False)
            nota.historia = historia
            nota.doctor = request.user
            nota.save()
            messages.success(request, 'Nota clínica guardada.')
            return redirect('clinico:historia', paciente_pk=paciente_pk)
    else:
        form = NotaClinicaForm()

    return render(request, 'clinico/historia.html', {
        'paciente': paciente,
        'historia': historia,
        'notas': notas,
        'form': form,
    })


@login_required
def lista_tratamientos(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    tratamientos = (
        Tratamiento.objects
        .filter(paciente=paciente)
        .select_related('servicio', 'servicio__categoria', 'doctor')
        .prefetch_related('citas__doctor', 'citas__servicio')
        .order_by('-created_at')
    )

    servicios = Servicio.objects.filter(activo=True).select_related('categoria').order_by('categoria__nombre', 'nombre')

    if request.method == 'POST':
        form = TratamientoForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.paciente = paciente
            t.doctor = request.user
            t.save()
            messages.success(request, 'Tratamiento registrado.')
            return redirect('clinico:tratamientos', paciente_pk=paciente_pk)
    else:
        form = TratamientoForm()

    servicios_json = json.dumps([{
        'pk':       s.pk,
        'nombre':   s.nombre,
        'precio':   float(s.precio),
        'duracion': s.duracion_minutos,
        'desc':     s.descripcion[:80] if s.descripcion else '',
        'cat':      s.categoria.nombre if s.categoria else '',
        'color':    s.categoria.color  if s.categoria else '#6b7280',
    } for s in servicios])

    diente_groups = [
        ('Superior derecho', ['18','17','16','15','14','13','12','11']),
        ('Superior izquierdo', ['21','22','23','24','25','26','27','28']),
        ('Inferior derecho', ['48','47','46','45','44','43','42','41']),
        ('Inferior izquierdo', ['31','32','33','34','35','36','37','38']),
    ]

    trat_list = list(tratamientos)
    completados  = sum(1 for t in trat_list if t.estado == 'completado')
    en_proceso   = sum(1 for t in trat_list if t.estado == 'en_proceso')
    saldo_total  = sum(t.get_saldo_pendiente() for t in trat_list)

    return render(request, 'clinico/tratamientos.html', {
        'paciente':       paciente,
        'tratamientos':   trat_list,
        'form':           form,
        'servicios':      servicios,
        'servicios_json': servicios_json,
        'diente_groups':  diente_groups,
        'completados':    completados,
        'en_proceso':     en_proceso,
        'saldo_total':    saldo_total,
    })


@login_required
def eliminar_tratamiento(request, pk):
    tratamiento = get_object_or_404(Tratamiento, pk=pk)
    paciente_pk = tratamiento.paciente.pk
    if request.method == 'POST':
        tratamiento.delete()
        messages.success(request, 'Tratamiento eliminado.')
    return redirect('clinico:tratamientos', paciente_pk=paciente_pk)


@login_required
def actualizar_estado_tratamiento(request, pk):
    tratamiento = get_object_or_404(Tratamiento, pk=pk)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Tratamiento.ESTADO_CHOICES):
            tratamiento.estado = nuevo_estado
            tratamiento.save()
            messages.success(request, 'Estado actualizado.')
    return redirect('clinico:tratamientos', paciente_pk=tratamiento.paciente.pk)


@login_required
@solo_admin
def lista_servicios(request):
    mostrar_inactivos = request.GET.get('inactivos') == '1'
    servicios = (
        Servicio.objects
        .select_related('categoria')
        .order_by('categoria__nombre', 'nombre')
    ) if mostrar_inactivos else (
        Servicio.objects.filter(activo=True)
        .select_related('categoria')
        .order_by('categoria__nombre', 'nombre')
    )
    categorias = CategoriaServicio.objects.all().order_by('nombre')

    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Servicio creado.')
            return redirect('clinico:servicios')
    else:
        form = ServicioForm()

    return render(request, 'clinico/servicios.html', {
        'servicios':        servicios,
        'categorias':       categorias,
        'form':             form,
        'mostrar_inactivos': mostrar_inactivos,
    })


@login_required
@solo_admin
def editar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk)
    if request.method == 'GET':
        # Devuelve los datos actuales del servicio como JSON para el modal
        return JsonResponse({
            'pk':               servicio.pk,
            'nombre':           servicio.nombre,
            'descripcion':      servicio.descripcion,
            'precio':           str(servicio.precio),
            'duracion_minutos': servicio.duracion_minutos,
            'categoria_pk':     servicio.categoria_id or '',
        })
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        if form.is_valid():
            form.save()
            messages.success(request, f'Servicio "{servicio.nombre}" actualizado.')
        else:
            messages.error(request, 'Error al guardar. Revisa los campos.')
        return redirect('clinico:servicios')


@login_required
def toggle_servicio(request, pk):
    if request.method == 'POST':
        servicio = get_object_or_404(Servicio, pk=pk)
        servicio.activo = not servicio.activo
        servicio.save(update_fields=['activo'])
        estado = 'habilitado' if servicio.activo else 'deshabilitado'
        messages.success(request, f'Servicio "{servicio.nombre}" {estado}.')
    return redirect('clinico:servicios')
