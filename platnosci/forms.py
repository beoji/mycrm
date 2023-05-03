from django.forms import ModelForm, Form
from django import forms
from escrm.models import Platnosc


class PlatnoscForm(ModelForm):

    class Meta(ModelForm):
        model = Platnosc
        exclude = ['umowa']

