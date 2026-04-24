from django import forms
from django.core.exceptions import ValidationError
from .models import Cita, Sillon
from pacientes.models import Paciente
from clinico.models import Servicio
from django.contrib.auth.models import User
from facturacion.models import MetodoPago


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['paciente', 'doctor', 'servicio', 'tratamiento',
                  'fecha', 'hora_inicio', 'hora_fin', 'motivo', 'notas']
        widgets = {
            'paciente':    forms.Select(attrs={'class': 'form-select'}),
            'doctor':      forms.Select(attrs={'class': 'form-select'}),
            'servicio':    forms.Select(attrs={'class': 'form-select'}),
            'tratamiento': forms.HiddenInput(),
            'fecha':       forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin':    forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'motivo':      forms.TextInput(attrs={'class': 'form-control'}),
            'notas':       forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['doctor'].queryset = User.objects.filter(
            perfil__rol__in=['dentista', 'admin'],
            perfil__activo=True
        )

        if user is not None:
            es_admin = hasattr(user, 'perfil') and user.perfil.rol == 'admin'
            if not es_admin:
                # Doctor por defecto: el usuario actual
                if not self.initial.get('doctor') and not self.data.get('doctor'):
                    self.initial['doctor'] = user.pk

                # Pacientes: solo los que han tenido citas con este doctor
                from agenda.models import Cita as _Cita
                ids = _Cita.objects.filter(doctor=user).values_list('paciente_id', flat=True).distinct()
                self.fields['paciente'].queryset = Paciente.objects.filter(
                    pk__in=ids, activo=True
                ).order_by('apellidos', 'nombres')

    def clean(self):
        cleaned = super().clean()
        doctor      = cleaned.get('doctor')
        fecha       = cleaned.get('fecha')
        hora_inicio = cleaned.get('hora_inicio')
        hora_fin    = cleaned.get('hora_fin')

        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise ValidationError('La hora de fin debe ser posterior a la hora de inicio.')

        if doctor and fecha and hora_inicio and hora_fin:
            conflictos = Cita.objects.filter(
                doctor=doctor,
                fecha=fecha,
                estado__in=['programada', 'confirmada', 'en_curso'],
                hora_fin__gt=hora_inicio,
                hora_inicio__lt=hora_fin,
            )
            if self.instance and self.instance.pk:
                conflictos = conflictos.exclude(pk=self.instance.pk)

            if conflictos.exists():
                c = conflictos.select_related('paciente').first()
                nombre_doc = doctor.get_full_name() or doctor.username
                raise ValidationError(
                    f'El Dr./Dra. {nombre_doc} ya tiene una cita de '
                    f'{c.hora_inicio.strftime("%H:%M")} a {c.hora_fin.strftime("%H:%M")} '
                    f'con {c.paciente} el {fecha.strftime("%d/%m/%Y")}. '
                    f'Elige otro horario o selecciona un doctor disponible.'
                )

        return cleaned


class CobrarCitaForm(forms.Form):
    metodo_pago = forms.ModelChoiceField(
        queryset=MetodoPago.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Método de pago',
    )
    descuento = forms.DecimalField(
        required=False, initial=0, min_value=0, max_value=100,
        label='Descuento (%)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'step': '0.01',
            'min': '0', 'max': '100', 'id': 'id_descuento',
        }),
    )
    monto = forms.DecimalField(
        min_value=0, max_digits=10, decimal_places=2,
        label='Monto a cobrar (Bs)',
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'step': '0.01', 'id': 'id_monto',
        }),
    )
    concepto = forms.CharField(
        max_length=300,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Concepto',
    )
    numero_recibo = forms.CharField(
        required=False, max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='N° de recibo',
    )
    notas = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label='Notas',
    )


class SillonForm(forms.ModelForm):
    class Meta:
        model = Sillon
        fields = ['nombre', 'descripcion', 'color']
        widgets = {
            'nombre':      forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'color':       forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }
