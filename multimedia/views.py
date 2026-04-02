from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from pacientes.models import Paciente
from .models import FotoClinica, ComparacionFotos
from .forms import FotoClinicaForm, ComparacionForm


@login_required
def galeria_paciente(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    fotos = FotoClinica.objects.filter(paciente=paciente).order_by('-fecha')
    comparaciones = ComparacionFotos.objects.filter(paciente=paciente).select_related('foto_antes', 'foto_despues')

    if request.method == 'POST':
        form = FotoClinicaForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.paciente = paciente
            foto.subido_por = request.user
            foto.save()
            messages.success(request, 'Imagen subida correctamente.')
            return redirect('multimedia:galeria', paciente_pk=paciente_pk)
    else:
        form = FotoClinicaForm()

    return render(request, 'multimedia/galeria.html', {
        'paciente': paciente, 'fotos': fotos,
        'comparaciones': comparaciones, 'form': form,
    })


@login_required
def crear_comparacion(request, paciente_pk):
    paciente = get_object_or_404(Paciente, pk=paciente_pk)
    if request.method == 'POST':
        form = ComparacionForm(request.POST)
        form.fields['foto_antes'].queryset = FotoClinica.objects.filter(paciente=paciente)
        form.fields['foto_despues'].queryset = FotoClinica.objects.filter(paciente=paciente)
        if form.is_valid():
            comp = form.save(commit=False)
            comp.paciente = paciente
            comp.save()
            messages.success(request, 'Comparación creada.')
    return redirect('multimedia:galeria', paciente_pk=paciente_pk)
