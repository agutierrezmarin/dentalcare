from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import PerfilUsuario
from .forms import PerfilUsuarioForm, CrearUsuarioForm, EditarUsuarioForm, MiPerfilInfoForm, MiPerfilPasswordForm


@login_required
def lista_personal(request):
    from agenda.models import Cita
    from django.db.models import Count, Q
    from django.utils import timezone

    personal = (PerfilUsuario.objects
                .select_related('user')
                .order_by('-activo', 'user__last_name', 'user__first_name'))

    hoy = timezone.now().date()

    # Stats de citas por doctor en una sola query
    stats = (
        Cita.objects
        .filter(doctor__isnull=False)
        .values('doctor_id')
        .annotate(
            total=Count('id'),
            hoy=Count('id', filter=Q(fecha=hoy)),
            completadas=Count('id', filter=Q(estado='completada')),
        )
    )
    stats_map = {s['doctor_id']: s for s in stats}

    enriched = []
    for p in personal:
        s = stats_map.get(p.user_id, {})
        enriched.append({
            'p':          p,
            'total':      s.get('total', 0),
            'hoy':        s.get('hoy', 0),
            'completadas': s.get('completadas', 0),
        })

    return render(request, 'personal/lista.html', {'enriched': enriched})


@login_required
def crear_personal(request):
    if request.method == 'POST':
        u_form = CrearUsuarioForm(request.POST)
        p_form = PerfilUsuarioForm(request.POST, request.FILES)
        if u_form.is_valid() and p_form.is_valid():
            user = u_form.save()
            # La señal en signals.py auto-crea un PerfilUsuario al guardar el User.
            # Recuperamos ese perfil y lo actualizamos para evitar IntegrityError
            # por violación de unicidad en user_id.
            perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
            p = p_form.save(commit=False)
            perfil.rol          = p.rol
            perfil.telefono     = p.telefono
            perfil.especialidad = p.especialidad
            perfil.color_agenda = p.color_agenda
            if 'foto' in request.FILES:
                perfil.foto = request.FILES['foto']
            perfil.save()
            messages.success(request, f'Usuario {user.get_full_name() or user.username} creado correctamente.')
            return redirect('personal:lista')
    else:
        u_form = CrearUsuarioForm()
        p_form = PerfilUsuarioForm()
    return render(request, 'personal/form.html', {
        'u_form': u_form,
        'p_form': p_form,
        'titulo': 'Nuevo usuario',
    })


@login_required
def editar_personal(request, pk):
    perfil = get_object_or_404(PerfilUsuario, pk=pk)
    user   = perfil.user
    if request.method == 'POST':
        u_form = EditarUsuarioForm(request.POST, instance=user)
        p_form = PerfilUsuarioForm(request.POST, request.FILES, instance=perfil)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Usuario {user.get_full_name() or user.username} actualizado.')
            return redirect('personal:lista')
    else:
        u_form = EditarUsuarioForm(instance=user)
        p_form = PerfilUsuarioForm(instance=perfil)
    return render(request, 'personal/form.html', {
        'u_form': u_form,
        'p_form': p_form,
        'titulo': 'Editar usuario',
        'perfil': perfil,
    })


@login_required
def mi_perfil(request):
    """Perfil propio: cualquier usuario puede ver y editar su información."""
    from django.contrib.auth import update_session_auth_hash

    user   = request.user
    perfil, _ = PerfilUsuario.objects.get_or_create(user=user)

    info_form     = MiPerfilInfoForm()
    password_form = MiPerfilPasswordForm()
    accion_error  = None

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'info':
            info_form = MiPerfilInfoForm(request.POST)
            if info_form.is_valid():
                d = info_form.cleaned_data
                user.first_name  = d['first_name']
                user.last_name   = d['last_name']
                user.email       = d['email']
                user.save(update_fields=['first_name', 'last_name', 'email'])
                perfil.telefono     = d['telefono']
                perfil.especialidad = d['especialidad']
                if d['color_agenda']:
                    perfil.color_agenda = d['color_agenda']
                if 'foto' in request.FILES:
                    perfil.foto = request.FILES['foto']
                perfil.save()
                messages.success(request, 'Perfil actualizado correctamente.')
                return redirect('personal:mi_perfil')

        elif accion == 'foto':
            if 'foto' in request.FILES:
                perfil.foto = request.FILES['foto']
                perfil.save(update_fields=['foto'])
                messages.success(request, 'Foto de perfil actualizada.')
            return redirect('personal:mi_perfil')

        elif accion == 'password':
            password_form = MiPerfilPasswordForm(request.POST)
            if password_form.is_valid():
                actual = password_form.cleaned_data['password_actual']
                nueva  = password_form.cleaned_data['nueva_password']
                if user.check_password(actual):
                    user.set_password(nueva)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Contraseña cambiada correctamente.')
                    return redirect('personal:mi_perfil')
                else:
                    password_form.add_error('password_actual', 'La contraseña actual no es correcta.')
            accion_error = 'password'
    else:
        info_form = MiPerfilInfoForm(initial={
            'first_name':   user.first_name,
            'last_name':    user.last_name,
            'email':        user.email,
            'telefono':     perfil.telefono,
            'especialidad': perfil.especialidad,
            'color_agenda': perfil.color_agenda,
        })

    return render(request, 'personal/perfil.html', {
        'perfil':        perfil,
        'info_form':     info_form,
        'password_form': password_form,
        'accion_error':  accion_error,
        'titulo':        'Mi perfil',
    })


@login_required
def desactivar_personal(request, pk):
    """Activa o desactiva un usuario (toggle). Solo acepta POST."""
    if request.method == 'POST':
        perfil = get_object_or_404(PerfilUsuario, pk=pk)
        perfil.activo = not perfil.activo
        perfil.save()
        estado = 'activado' if perfil.activo else 'desactivado'
        messages.success(request, f'Usuario {perfil.user.get_full_name() or perfil.user.username} {estado}.')
    return redirect('personal:lista')
