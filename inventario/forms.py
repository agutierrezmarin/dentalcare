from django import forms
from .models import Insumo, MovimientoInventario


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = ['categoria', 'nombre', 'descripcion', 'unidad', 'stock_actual', 'stock_minimo', 'precio_unitario', 'proveedor']
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'}) for f in ['nombre', 'descripcion', 'proveedor']}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in self.fields:
                continue
            widget = self.fields[field].widget
            if not hasattr(widget, 'attrs'):
                continue
            if 'class' not in widget.attrs:
                widget.attrs['class'] = 'form-control'


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['tipo', 'cantidad', 'motivo']
        widgets = {
            'tipo':     forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'motivo':   forms.TextInput(attrs={'class': 'form-control'}),
        }
