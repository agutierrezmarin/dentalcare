from django import forms
from .models import Paciente, Alergia, AdjuntoPaciente


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nombres', 'apellidos', 'fecha_nacimiento', 'sexo', 'ci',
            'tipo_sangre', 'telefono', 'telefono_emergencia', 'contacto_emergencia',
            'email', 'direccion', 'alergias', 'medicamentos_actuales',
            'enfermedades_cronicas', 'observaciones', 'foto'
        ]
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'ci': forms.TextInput(attrs={'class': 'form-control'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_sangre': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medicamentos_actuales': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'enfermedades_cronicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AlergiaForm(forms.ModelForm):
    class Meta:
        model = Alergia
        fields = ['tipo', 'descripcion', 'reaccion', 'gravedad']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
            'reaccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'gravedad': forms.Select(attrs={'class': 'form-select'}),
        }


class AdjuntoForm(forms.ModelForm):
    class Meta:
        model = AdjuntoPaciente
        fields = ['tipo', 'titulo', 'archivo', 'descripcion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PacienteRapidoForm(forms.ModelForm):
    """Registro mínimo de paciente desde el formulario de nueva cita."""
    class Meta:
        model  = Paciente
        fields = ['nombres', 'apellidos', 'ci', 'telefono', 'sexo', 'fecha_nacimiento']
        widgets = {
            'nombres':          forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'apellidos':        forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'ci':               forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'telefono':         forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'sexo':             forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'}),
        }

    def clean_ci(self):
        ci = self.cleaned_data.get('ci', '').strip()
        return ci if ci else None
