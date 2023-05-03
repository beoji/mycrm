from django import forms
from escrm.models import Profil
from django.contrib.auth.models import User


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfilForm(forms.ModelForm):
    class Meta:
        model = Profil
        fields = ('telefon', 'stanowisko')
