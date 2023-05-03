from django.forms import ModelForm
from escrm.models import Platnosc


class PlatnoscForm(ModelForm):

    class Meta(ModelForm):
        model = Platnosc
        exclude = ['umowa']

