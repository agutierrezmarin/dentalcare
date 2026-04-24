from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

from .models import EspacioClinico, MantenimientoEspacio
from .forms import EspacioClinicoForm, MantenimientoForm
from dentalcare.decorators import solo_admin

User = get_user_model()


@login_required
@solo_admin
def lista_espacios(request):
    espacios = EspacioClinico.objects.filter(activo=True).prefetch_related('doctores__perfil')
    return render(request, 'espacios/lista.html', {'espacios': espacios})


@login_required
@solo_admin
def crear_espacio(request):
    if request.method == 'POST':
        form = EspacioClinicoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Espacio registrado exitosamente.')
            return redirect('espacios:lista')
    else:
        form = EspacioClinicoForm()
    return render(request, 'espacios/form.html', {'form': form, 'titulo': 'Nuevo espacio'})


@login_required
@solo_admin
def editar_espacio(request, pk):
    espacio = get_object_or_404(EspacioClinico, pk=pk)
    if request.method == 'POST':
        form = EspacioClinicoForm(request.POST, instance=espacio)
        if form.is_valid():
            form.save()
            messages.success(request, f'Espacio "{espacio.nombre}" actualizado.')
            return redirect('espacios:detalle', pk=espacio.pk)
    else:
        form = EspacioClinicoForm(instance=espacio)
    return render(request, 'espacios/form.html', {
        'form': form,
        'titulo': f'Editar: {espacio.nombre}',
        'espacio': espacio,
    })


@login_required
@solo_admin
def detalle_espacio(request, pk):
    espacio = get_object_or_404(EspacioClinico, pk=pk)
    mantenimientos = espacio.mantenimientos.select_related('registrado_por')
    form_mant = MantenimientoForm()
    return render(request, 'espacios/detalle.html', {
        'espacio':        espacio,
        'mantenimientos': mantenimientos,
        'form_mant':      form_mant,
    })


@login_required
@solo_admin
def registrar_mantenimiento(request, pk):
    espacio = get_object_or_404(EspacioClinico, pk=pk)
    if request.method == 'POST':
        form = MantenimientoForm(request.POST)
        if form.is_valid():
            mant = form.save(commit=False)
            mant.espacio = espacio
            mant.registrado_por = request.user
            mant.save()
            # Actualizar estado y próxima revisión del espacio
            espacio.estado = 'mantenimiento' if mant.tipo in ('correctivo', 'reparacion') else espacio.estado
            if mant.proxima_revision:
                espacio.proxima_revision = mant.proxima_revision
            espacio.save()
            messages.success(request, 'Mantenimiento registrado.')
        else:
            messages.warning(request, 'Datos inválidos en el formulario.')
    return redirect('espacios:detalle', pk=pk)


@login_required
@solo_admin
def cambiar_estado(request, pk):
    espacio = get_object_or_404(EspacioClinico, pk=pk)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        opciones_validas = [c[0] for c in EspacioClinico.ESTADO_CHOICES]
        if nuevo_estado in opciones_validas:
            espacio.estado = nuevo_estado
            espacio.save()
            messages.success(request, f'Estado actualizado a "{espacio.get_estado_display()}".')
    return redirect('espacios:lista')


@login_required
@solo_admin
def eliminar_espacio(request, pk):
    espacio = get_object_or_404(EspacioClinico, pk=pk)
    if request.method == 'POST':
        nombre = espacio.nombre
        espacio.activo = False
        espacio.save()
        messages.success(request, f'Espacio "{nombre}" desactivado.')
    return redirect('espacios:lista')
