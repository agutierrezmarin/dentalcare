from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
import json
from pacientes.models import Paciente
from .models import (
    Odontograma, EstadoDiente, HistoriaClinica,
    NotaClinica, Tratamiento, Servicio, CategoriaServicio
)
from .forms import TratamientoForm, NotaClinicaForm, ServicioForm


@login_required
def odontograma(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    odontogramas = Odontograma.objects.filter(paciente=paciente).prefetch_related('estados')

    # Último odontograma activo o crear uno nuevo
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

    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    data = json.loads(request.body)

    odontograma_obj = Odontograma.objects.create(
        paciente=paciente,
        creado_por=request.user,
        notas=data.get('notas', '')
    )

    for item in data.get('estados', []):
        EstadoDiente.objects.create(
            odontograma=odontograma_obj,
            numero_diente=item['diente'],
            condicion=item['condicion'],
            cara=item.get('cara', 'general'),
            notas=item.get('notas', ''),
            color_hex=item.get('color', '#22d3ee'),
        )

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

    return render(request, 'clinico/tratamientos.html', {
        'paciente':      paciente,
        'tratamientos':  tratamientos,
        'form':          form,
        'servicios':     servicios,
        'servicios_json': servicios_json,
    })


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
