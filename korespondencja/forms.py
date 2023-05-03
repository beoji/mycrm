from django import forms
from escrm.models import Korespondencja, AdresatNadawca


class KorespondencjaForm(forms.ModelForm):
    # adresat_nadawca = forms.CharField()

    class Meta(forms.ModelForm):
        model = Korespondencja
        exclude = ['id_korespondencji', 'data_dodania', 'adresat_nadawca', 'uzytkownik']
        widgets = {'data_przyjscia_wyjscia': forms.widgets.DateInput(attrs={'type': 'date'})}


class AdresatNadawcaForm(forms.ModelForm):

    class Meta(forms.ModelForm):
        model = AdresatNadawca
        fields = '__all__'
