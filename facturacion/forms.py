from django import forms
from .models import Pago, PlanPago, Presupuesto


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['paciente', 'metodo_pago', 'monto', 'fecha', 'concepto', 'numero_recibo', 'notas']
        widgets = {
            'paciente':      forms.Select(attrs={'class': 'form-select'}),
            'metodo_pago':   forms.Select(attrs={'class': 'form-select'}),
            'monto':         forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha':         forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'concepto':      forms.TextInput(attrs={'class': 'form-control'}),
            'numero_recibo': forms.TextInput(attrs={'class': 'form-control'}),
            'notas':         forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PlanPagoForm(forms.ModelForm):
    class Meta:
        model = PlanPago
        fields = ['numero_cuota', 'monto', 'fecha_vencimiento']
        widgets = {
            'numero_cuota':      forms.NumberInput(attrs={'class': 'form-control'}),
            'monto':             forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['notas']
        widgets = {
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
