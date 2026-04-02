from django import forms
from .models import Cita, Sillon
from pacientes.models import Paciente
from clinico.models import Servicio
from django.contrib.auth.models import User
from facturacion.models import MetodoPago


class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['paciente', 'doctor', 'sillon', 'servicio', 'tratamiento',
                  'fecha', 'hora_inicio', 'hora_fin', 'motivo', 'notas']
        widgets = {
            'paciente':    forms.Select(attrs={'class': 'form-select'}),
            'doctor':      forms.Select(attrs={'class': 'form-select'}),
            'sillon':      forms.Select(attrs={'class': 'form-select'}),
            'servicio':    forms.Select(attrs={'class': 'form-select'}),
            'tratamiento': forms.HiddenInput(),
            'fecha':       forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin':    forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'motivo':      forms.TextInput(attrs={'class': 'form-control'}),
            'notas':       forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = User.objects.filter(
            perfil__rol__in=['dentista', 'admin'],
            perfil__activo=True
        )


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
