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

    def clean_ci(self):
        ci = self.cleaned_data.get('ci', '').strip()
        if not ci:
            return None
        qs = Paciente.objects.filter(ci=ci)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        existente = qs.first()
        if existente:
            self._paciente_dup = existente
            raise forms.ValidationError(
                f'Ya existe un paciente registrado con esta C.I.: {existente}'
            )
        return ci

    def clean(self):
        cleaned_data = super().clean()
        # Only check name+dob when no CI was submitted at all
        if self.data.get('ci', '').strip():
            return cleaned_data
        nombres   = (cleaned_data.get('nombres')   or '').strip()
        apellidos = (cleaned_data.get('apellidos') or '').strip()
        fecha     = cleaned_data.get('fecha_nacimiento')
        if nombres and apellidos and fecha:
            qs = Paciente.objects.filter(
                nombres__iexact=nombres, apellidos__iexact=apellidos,
                fecha_nacimiento=fecha
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            existente = qs.first()
            if existente:
                self._paciente_dup = existente
                raise forms.ValidationError(
                    f'Ya existe un paciente con ese nombre y fecha de nacimiento: {existente}'
                )
        return cleaned_data


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
        if not ci:
            return None
        # Detect CI duplicate — store it but do NOT raise; get_or_create_paciente() will reuse
        existente = Paciente.objects.filter(ci=ci).first()
        if existente:
            self._paciente_dup = existente
        return ci

    def clean(self):
        cleaned_data = super().clean()
        # If CI already matched an existing patient, skip name+dob check
        if getattr(self, '_paciente_dup', None):
            return cleaned_data
        # No CI provided — check name + apellido + fecha_nacimiento
        if not self.data.get('ci', '').strip():
            nombres   = (cleaned_data.get('nombres')   or '').strip()
            apellidos = (cleaned_data.get('apellidos') or '').strip()
            fecha     = cleaned_data.get('fecha_nacimiento')
            if nombres and apellidos and fecha:
                existente = Paciente.objects.filter(
                    nombres__iexact=nombres, apellidos__iexact=apellidos,
                    fecha_nacimiento=fecha
                ).first()
                if existente:
                    self._paciente_dup = existente
        return cleaned_data

    def validate_unique(self):
        # Skip DB uniqueness check on 'ci' when we already know we'll reuse the existing patient
        if getattr(self, '_paciente_dup', None):
            return
        super().validate_unique()

    def get_or_create_paciente(self):
        """Returns (paciente, creado). Uses existing patient if CI or name+dob matches."""
        dup = getattr(self, '_paciente_dup', None)
        if dup:
            return dup, False
        return self.save(), True
