from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


def _admins():
    return list(User.objects.filter(perfil__rol='admin', perfil__activo=True))


def _recepcion():
    return list(User.objects.filter(perfil__rol='recepcion', perfil__activo=True))


def _juntar(*grupos):
    """Combina listas de usuarios eliminando duplicados por pk."""
    seen = set()
    result = []
    for grupo in grupos:
        items = [grupo] if isinstance(grupo, User) else grupo
        for user in items:
            if user is not None and user.pk not in seen:
                seen.add(user.pk)
                result.append(user)
    return result


def _notificar(destinatarios, cita, tipo, titulo, mensaje):
    from .models import NotificacionAgenda
    for user in destinatarios:
        NotificacionAgenda.objects.create(
            destinatario=user,
            cita=cita,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
        )


def notificar_reagendada(cita):
    """Llamado manualmente desde mover_cita (drag & drop)."""
    paciente_str = str(cita.paciente)
    fecha_str = cita.fecha.strftime('%d/%m/%Y')
    hora_str = cita.hora_inicio.strftime('%H:%M')
    doctor_str = cita.doctor.get_full_name() if cita.doctor else 'Sin doctor'
    destinatarios = _juntar(
        _admins(),
        _recepcion(),
        cita.doctor,
    )
    _notificar(
        destinatarios,
        cita,
        'reagendada',
        f'Cita reagendada — {paciente_str}',
        f'La cita de {paciente_str} con {doctor_str} fue movida al {fecha_str} a las {hora_str}.',
    )


@receiver(post_save, sender='agenda.Cita')
def notificar_cambios_cita(sender, instance, created, **kwargs):
    cita = instance
    paciente_str = str(cita.paciente)
    fecha_str = cita.fecha.strftime('%d/%m/%Y')
    hora_str = cita.hora_inicio.strftime('%H:%M')
    doctor_str = cita.doctor.get_full_name() if cita.doctor else 'Sin doctor asignado'

    if created:
        # Nueva cita → doctor + admins + recepcion
        destinatarios = _juntar(_admins(), _recepcion(), cita.doctor)
        if destinatarios:
            _notificar(
                destinatarios,
                cita,
                'nueva_cita',
                f'Nueva cita — {paciente_str}',
                f'Se agendó una cita con {paciente_str} para {doctor_str} '
                f'el {fecha_str} a las {hora_str}.',
            )
        return

    # Cambios de estado — requiere _estado_original set en Cita.__init__
    estado_anterior = getattr(cita, '_estado_original', None)
    if estado_anterior is None or estado_anterior == cita.estado:
        return

    estado = cita.estado

    if estado == 'confirmada':
        # Doctor + admins
        destinatarios = _juntar(_admins(), cita.doctor)
        _notificar(
            destinatarios,
            cita,
            'confirmada',
            f'Cita confirmada — {paciente_str}',
            f'{paciente_str} confirmó su cita con {doctor_str} '
            f'el {fecha_str} a las {hora_str}.',
        )

    elif estado == 'en_curso':
        # Solo admins — informativo de flujo operativo
        _notificar(
            _admins(),
            cita,
            'confirmada',
            f'Cita en curso — {paciente_str}',
            f'La cita de {paciente_str} con {doctor_str} '
            f'inició a las {hora_str}.',
        )

    elif estado == 'cancelada':
        destinatarios = _juntar(_admins(), _recepcion(), cita.doctor)
        _notificar(
            destinatarios,
            cita,
            'cancelada',
            f'Cita cancelada — {paciente_str}',
            f'La cita de {paciente_str} con {doctor_str} '
            f'del {fecha_str} a las {hora_str} fue cancelada.',
        )

    elif estado == 'no_asistio':
        destinatarios = _juntar(_admins(), _recepcion(), cita.doctor)
        _notificar(
            destinatarios,
            cita,
            'no_asistio',
            f'Paciente no asistió — {paciente_str}',
            f'{paciente_str} no asistió a su cita con {doctor_str} '
            f'del {fecha_str} a las {hora_str}.',
        )
