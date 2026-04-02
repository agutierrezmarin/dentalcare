from django import forms
from .models import Tratamiento, NotaClinica, Servicio


class TratamientoForm(forms.ModelForm):
    class Meta:
        model = Tratamiento
        fields = ['servicio', 'numero_diente', 'precio_acordado', 'fecha_inicio', 'notas']
        widgets = {
            'servicio': forms.Select(attrs={'class': 'form-select'}),
            'numero_diente': forms.NumberInput(attrs={'class': 'form-control', 'min': 11, 'max': 85}),
            'precio_acordado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class NotaClinicaForm(forms.ModelForm):
    class Meta:
        model = NotaClinica
        fields = ['motivo', 'hallazgos', 'diagnostico', 'plan_tratamiento']
        widgets = {
            'motivo': forms.TextInput(attrs={'class': 'form-control'}),
            'hallazgos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnostico': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'plan_tratamiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['categoria', 'nombre', 'descripcion', 'precio', 'duracion_minutos']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracion_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
        }
