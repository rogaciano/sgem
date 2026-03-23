from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth.models import User
from django import forms


class UsuarioCreateForm(UserCreationForm):
    first_name = forms.CharField(label='Nome', max_length=100, required=True)
    last_name = forms.CharField(label='Sobrenome', max_length=100, required=False)
    email = forms.EmailField(label='E-mail', required=False)
    is_staff = forms.BooleanField(label='Acesso ao Admin', required=False)
    is_superuser = forms.BooleanField(label='Superusuário (acesso total)', required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'password1', 'password2', 'is_staff', 'is_superuser', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full bg-gray-800 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-orange-500/50 transition-all'})
        # Checkboxes mantém estilo próprio
        for fname in ['is_staff', 'is_superuser', 'is_active']:
            if fname in self.fields:
                self.fields[fname].widget.attrs.update({'class': 'w-4 h-4 accent-orange-500'})


class UsuarioEditForm(forms.ModelForm):
    first_name = forms.CharField(label='Nome', max_length=100, required=True)
    last_name = forms.CharField(label='Sobrenome', max_length=100, required=False)
    email = forms.EmailField(label='E-mail', required=False)
    is_staff = forms.BooleanField(label='Acesso ao Admin', required=False)
    is_superuser = forms.BooleanField(label='Superusuário (acesso total)', required=False)
    is_active = forms.BooleanField(label='Usuário ativo', required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'is_staff', 'is_superuser', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full bg-gray-800 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-orange-500/50 transition-all'})
        for fname in ['is_staff', 'is_superuser', 'is_active']:
            if fname in self.fields:
                self.fields[fname].widget.attrs.update({'class': 'w-4 h-4 accent-orange-500'})


class UsuarioSenhaForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'w-full bg-gray-800 border border-white/10 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:border-orange-500/50 transition-all'})
