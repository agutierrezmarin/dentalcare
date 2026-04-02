from django import forms
from .models import FotoClinica, ComparacionFotos


class FotoClinicaForm(forms.ModelForm):
    class Meta:
        model = FotoClinica
        fields = ['tipo', 'titulo', 'imagen', 'descripcion', 'numero_diente']
        widgets = {
            'tipo':          forms.Select(attrs={'class': 'form-select'}),
            'titulo':        forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion':   forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'numero_diente': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ComparacionForm(forms.ModelForm):
    class Meta:
        model = ComparacionFotos
        fields = ['titulo', 'foto_antes', 'foto_despues', 'notas']
        widgets = {
            'titulo':       forms.TextInput(attrs={'class': 'form-control'}),
            'foto_antes':   forms.Select(attrs={'class': 'form-select'}),
            'foto_despues': forms.Select(attrs={'class': 'form-select'}),
            'notas':        forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
