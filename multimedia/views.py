import io
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from pacientes.models import Paciente
from .models import FotoClinica, ComparacionFotos
from .forms import FotoClinicaForm, ComparacionForm


def _compress_image(image_field, max_px=1600, quality=82):
    """Redimensiona y comprime la imagen antes de guardarla."""
    try:
        from PIL import Image
        img = Image.open(image_field)
        # Convertir modos incompatibles con JPEG
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        # Reducir si supera max_px en cualquier dimensión
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True)
        buf.seek(0)
        # Usar solo el nombre de archivo base (sin ruta) para evitar que
        # Django duplique el path al anteponer upload_to al guardar
        basename = image_field.name.rsplit('/', 1)[-1]
        name = basename.rsplit('.', 1)[0] + '.jpg'
        return ContentFile(buf.read(), name=name)
    except Exception:
        # Si falla la compresión, usar la imagen original sin cambios
        return None


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
            # Nota: Django ya guarda el archivo original en disco durante is_valid()
            # (_post_clean → save_form_data). Hay que eliminar ese original y
            # reemplazarlo con la versión comprimida.
            original = foto.imagen  # ImageFieldFile ya guardado en disco
            compressed = _compress_image(original)
            if compressed is not None:
                try:
                    original.delete(save=False)   # borra el archivo original del disco
                except Exception:
                    pass
                foto.imagen = compressed          # ContentFile con nombre corto
            foto.save()
            messages.success(request, 'Imagen subida y optimizada correctamente.')
            return redirect('multimedia:galeria', paciente_pk=paciente_pk)
    else:
        form = FotoClinicaForm()

    return render(request, 'multimedia/galeria.html', {
        'paciente':      paciente,
        'fotos':         fotos,
        'comparaciones': comparaciones,
        'form':          form,
        'total_fotos':   fotos.count(),
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
            messages.success(request, 'Comparación creada correctamente.')
        else:
            messages.error(request, 'Error al crear la comparación. Verifica los campos.')
    return redirect('multimedia:galeria', paciente_pk=paciente_pk)


@login_required
def eliminar_foto(request, foto_pk):
    foto = get_object_or_404(FotoClinica, pk=foto_pk)
    paciente_pk = foto.paciente_id
    if request.method == 'POST':
        foto.imagen.delete(save=False)
        foto.delete()
        messages.success(request, 'Foto eliminada.')
    return redirect('multimedia:galeria', paciente_pk=paciente_pk)


@login_required
def eliminar_comparacion(request, comp_pk):
    comp = get_object_or_404(ComparacionFotos, pk=comp_pk)
    paciente_pk = comp.paciente_id
    if request.method == 'POST':
        comp.delete()
        messages.success(request, 'Comparación eliminada.')
    return redirect('multimedia:galeria', paciente_pk=paciente_pk)
