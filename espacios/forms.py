from django import forms
from django.contrib.auth import get_user_model
from .models import EspacioClinico, MantenimientoEspacio

User = get_user_model()


class EspacioClinicoForm(forms.ModelForm):
    class Meta:
        model = EspacioClinico
        fields = [
            'nombre', 'tipo', 'descripcion',
            'ubicacion', 'capacidad', 'color',
            'estado', 'doctores', 'proxima_revision',
        ]
        widgets = {
            'nombre':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sillón 1, Consultorio Norte'}),
            'tipo':            forms.Select(attrs={'class': 'form-select'}),
            'descripcion':     forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ubicacion':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Planta baja, Piso 2'}),
            'capacidad':       forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'color':           forms.TextInput(attrs={'class': 'form-control form-control-color', 'type': 'color'}),
            'estado':          forms.Select(attrs={'class': 'form-select'}),
            'doctores':        forms.CheckboxSelectMultiple(),
            'proxima_revision':forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from personal.models import PerfilUsuario
            doctores_ids = PerfilUsuario.objects.filter(
                rol__in=('dentista', 'admin'), activo=True
            ).values_list('user_id', flat=True)
            self.fields['doctores'].queryset = User.objects.filter(
                id__in=doctores_ids
            ).order_by('first_name', 'last_name')
        except Exception:
            pass
        self.fields['doctores'].required = False


class MantenimientoForm(forms.ModelForm):
    class Meta:
        model = MantenimientoEspacio
        fields = ['tipo', 'descripcion', 'costo', 'realizado_por', 'fecha', 'proxima_revision']
        widgets = {
            'tipo':            forms.Select(attrs={'class': 'form-select'}),
            'descripcion':     forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                      'placeholder': 'Describe el trabajo realizado…'}),
            'costo':           forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'realizado_por':   forms.TextInput(attrs={'class': 'form-control',
                                                       'placeholder': 'Nombre del técnico o empresa'}),
            'fecha':           forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'proxima_revision':forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }
