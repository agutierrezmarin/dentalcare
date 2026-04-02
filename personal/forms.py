from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import PerfilUsuario


class CrearUsuarioForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name  = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email      = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True


class EditarUsuarioForm(forms.ModelForm):
    """Edita datos básicos del usuario. El campo nueva_password es opcional."""
    nueva_password = forms.CharField(
        required=False,
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class':       'form-control',
            'placeholder': 'Dejar vacío para no cambiar',
            'autocomplete': 'new-password',
        }),
    )

    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True

    def save(self, commit=True):
        user = super().save(commit=False)
        nueva = self.cleaned_data.get('nueva_password')
        if nueva:
            user.set_password(nueva)
        if commit:
            user.save()
        return user


class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model  = PerfilUsuario
        fields = ['rol', 'telefono', 'especialidad', 'color_agenda', 'foto']
        widgets = {
            'rol':          forms.Select(attrs={'class': 'form-select'}),
            'telefono':     forms.TextInput(attrs={'class': 'form-control'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control'}),
            'color_agenda': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
        }


class MiPerfilInfoForm(forms.Form):
    """Datos básicos del perfil (nombre, email, teléfono, especialidad, color)."""
    first_name  = forms.CharField(max_length=150, label='Nombre(s)',
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name   = forms.CharField(max_length=150, label='Apellidos',
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    email       = forms.EmailField(required=False, label='Correo electrónico',
                                   widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telefono    = forms.CharField(max_length=20, required=False, label='Teléfono',
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    especialidad= forms.CharField(max_length=100, required=False, label='Especialidad',
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    color_agenda= forms.CharField(max_length=7, required=False, label='Color en agenda',
                                  widget=forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}))


class MiPerfilPasswordForm(forms.Form):
    """Cambio de contraseña autenticado."""
    password_actual    = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'}))
    nueva_password     = forms.CharField(
        label='Nueva contraseña', min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}))
    confirmar_password = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}))

    def clean(self):
        data = super().clean()
        nueva  = data.get('nueva_password')
        confirmar = data.get('confirmar_password')
        if nueva and confirmar and nueva != confirmar:
            raise forms.ValidationError('Las contraseñas nuevas no coinciden.')
        return data
