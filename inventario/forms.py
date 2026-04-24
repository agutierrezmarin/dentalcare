from django import forms
from .models import Insumo, MovimientoInventario, CategoriaInsumo


class CategoriaInsumoForm(forms.ModelForm):
    class Meta:
        model = CategoriaInsumo
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la categoría'}),
        }


class InsumoForm(forms.ModelForm):
    class Meta:
        model = Insumo
        fields = [
            'categoria', 'nombre', 'descripcion', 'unidad',
            'stock_actual', 'stock_minimo', 'precio_unitario',
            'proveedor', 'fecha_vencimiento',
        ]
        widgets = {
            'nombre':            forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'proveedor':         forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if hasattr(widget, 'attrs') and 'class' not in widget.attrs:
                widget.attrs['class'] = 'form-control'
        # Select fields use form-select
        self.fields['categoria'].widget.attrs['class'] = 'form-select'
        self.fields['unidad'].widget.attrs['class'] = 'form-select'
        # Numeric fields
        for fname in ('stock_actual', 'stock_minimo', 'precio_unitario'):
            self.fields[fname].widget.attrs.update({'class': 'form-control', 'step': '0.01'})


class MovimientoForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['tipo', 'cantidad', 'motivo']
        widgets = {
            'tipo':     forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'motivo':   forms.TextInput(attrs={'class': 'form-control'}),
        }
