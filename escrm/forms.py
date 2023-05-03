from django import forms
from django.forms import ModelForm, Form

from .models import Kontrahent, AdresKontrahent, Osoba, AdresOsoba, Oferta, Umowa, Zdarzenie, Dokument
from .validators import *


class OfertaForm(ModelForm):
    class Meta(ModelForm):
        model = Oferta
        fields = ['temat', 'produkt', 'termin_waznosci', 'wartosc', 'status',
                  'data_sporzadzenia', 'kontrahent', 'waluta']
        widgets = {
            'kontrahent': forms.HiddenInput(),
            'data_sporzadzenia': forms.widgets.DateInput(attrs={'type': 'date'}),
            'termin_waznosci': forms.widgets.DateInput(attrs={'type': 'date'})
        }


class OfertaEditForm(ModelForm):
    class Meta(ModelForm):
        model = Oferta
        fields = ['temat', 'produkt', 'termin_waznosci', 'wartosc', 'waluta']
        widgets = {
            'termin_waznosci': forms.widgets.DateInput(attrs={'type': 'date'})
        }


class UmowaForm(ModelForm):
    wartosc = forms.IntegerField(validators=[validate_wartosc_umowa], label='Wartość')

    class Meta(ModelForm):
        model = Umowa
        fields = ['temat', 'produkt', 'termin_waznosci', 'wartosc', 'status',
                  'data_sporzadzenia', 'data_platnosci', 'kontrahent', 'waluta', 'termin_platnosci']
        widgets = {
            'kontrahent': forms.HiddenInput(),
            'data_sporzadzenia': forms.widgets.DateInput(attrs={'type': 'date'}),
            'termin_waznosci': forms.widgets.DateInput(attrs={'type': 'date'}),
            'data_platnosci': forms.widgets.DateInput(attrs={'type': 'date'}),
        }


TYPE_CHOICES = [('jednorazowa', 'Jednorazowa'),
                ('cykliczna', 'Cykliczna')]

CYCLIC_CHOICES = [('pierwszego', 'Pierwszego'),
                  ('ostatniego', 'Ostatniego'),
                  ('okreslonego', 'Okreslonego'),
                  ('od_do', 'Od-do'),
                  ('nnieokreslona', 'Nie do określenia')]


class PlatnoscForm(Form):
    type = forms.ChoiceField(choices=TYPE_CHOICES, widget=forms.RadioSelect(), label='Rodzaj', required=True)
    once_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}), label='Data płatności',
                                required=False)
    cyclic_end_date = forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date'}),
                                      label='Data cykliczna koniec', required=False)
    cyclic_type = forms.ChoiceField(choices=CYCLIC_CHOICES, widget=forms.RadioSelect(), label='Rodzaj', required=False)
    cyclic_day = forms.IntegerField(label='Data cykliczna dzień', required=False)
    cyclic_date_start = forms.IntegerField(label='Data cykliczna dzień od', required=False)
    cyclic_date_end = forms.IntegerField(label='Data cykliczna dzień do', required=False)


class OsobaForm(ModelForm):
    class Meta(ModelForm):
        model = Osoba
        fields = ['imie', 'nazwisko', 'stanowisko', 'notatka']
        widgets = {
            'notatka': forms.Textarea(attrs={'rows': 2}),
            # 'kontrahent': forms.HiddenInput(),
        }


class AdresOsobaForm(ModelForm):
    class Meta(ModelForm):
        model = AdresOsoba
        exclude = ['osoba', ]
        widgets = {
            'czy_domyslny': forms.HiddenInput(),
        }


class KontrahentForm(ModelForm):
    nip = forms.CharField(validators=[validate_nip])

    class Meta(ModelForm):
        model = Kontrahent
        fields = '__all__'


class ZdarzenieForm(ModelForm):
    class Meta(ModelForm):
        model = Zdarzenie
        fields = ['data_zdarzenia', 'temat', 'typ', 'notatka', 'kontrahent']
        widgets = {
            'kontrahent': forms.HiddenInput(),
            'data_zdarzenia': forms.widgets.DateInput(attrs={'type': 'date'})
        }


class DokumentForm(ModelForm):
    class Meta(ModelForm):
        model = Dokument
        fields = ['tytul_dokumentu', 'nazwa_pliku']


class AdresKontrahentForm(ModelForm):
    class Meta(ModelForm):
        model = AdresKontrahent
        exclude = ['kontrahent', 'czy_domyslny']


class AdresKontrahentFormNew(ModelForm):
    class Meta(ModelForm):
        model = AdresKontrahent
        # fields = '__all__'
        fields = ['kontrahent', 'czy_domyslny', 'miasto', 'kod_pocztowy', 'ulica']
        widgets = {
            'kontrahent': forms.HiddenInput(),
            'czy_domyslny': forms.HiddenInput(),
        }
