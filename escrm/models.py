from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.db.models import Avg
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from datetime import date
import os


class Profil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telefon = models.CharField(max_length=15, blank=True)
    stanowisko = models.CharField(max_length=100, blank=True)

    # Methods
    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name

    def is_opiekun_of(self, kontrahent):
        return kontrahent.opiekun == self


class Kontrahent(models.Model):

    # Fields
    id_kontrahenta = models.AutoField(primary_key=True)
    nazwa_krotka = models.CharField(max_length=50, verbose_name="Nazwa krótka")
    nazwa_dluga = models.CharField(max_length=255, verbose_name="Pełna nazwa")
    nip = models.CharField(max_length=10)
    opiekun = models.ForeignKey(Profil, null=True, blank=True, on_delete=models.SET_NULL)
    czy_aktywny = models.BooleanField(default=False)
    email = models.CharField(null=True, blank=True, max_length=255)
    telefon = models.CharField(null=True, blank=True, max_length=45)
    notatka = models.TextField(null=True, blank=True)

    # Methods
    def __str__(self):
        return self.nazwa_krotka

    def get_absolute_url(self):
        return reverse('escrm:kontrahent-detail', kwargs={'pk': self.pk})

    def get_last_oferty(self, last):
        return self.oferta_set.all().order_by('-data_sporzadzenia')[:last]


class TypAdresu(models.Model):

    id = models.AutoField(primary_key=True)
    nazwa = models.CharField(max_length=60, null=False, blank=False)

    # Methods
    def __str__(self):
        return self.nazwa


class AdresKontrahent(models.Model):

    id_adresu = models.AutoField(primary_key=True)
    miasto = models.CharField(max_length=45)
    kod_pocztowy = models.CharField(max_length=6)
    ulica = models.CharField(max_length=45)
    kontrahent = models.ForeignKey(Kontrahent, on_delete=models.CASCADE)
    czy_domyslny = models.BooleanField(default=False)
    typ_adresu = models.ForeignKey(TypAdresu, null=False, blank=False, on_delete=models.PROTECT, default=1)

    def __str__(self):
        return self.ulica + ', ' + self.miasto


@receiver(pre_save, sender=AdresKontrahent)
def change_default_kontrahent_adres(sender, instance, **kwargs):
    if instance.czy_domyslny:
        adresy = AdresKontrahent.objects.filter(kontrahent=instance.kontrahent)
        adresy.update(czy_domyslny=False)
        instance.czy_domyslny = True


class Osoba(models.Model):

    id_osoby = models.AutoField(primary_key=True)
    imie = models.CharField(max_length=60, verbose_name="Imię")
    nazwisko = models.CharField(max_length=60)
    stanowisko = models.CharField(max_length=100)
    notatka = models.TextField(null=True)
    kontrahent = models.ManyToManyField(Kontrahent)

    def __str__(self):
        return self.imie + ' ' + self.nazwisko

    def get_absolute_url(self):
        return reverse('escrm:osoba-detail', kwargs={'pk': self.pk})


class AdresOsoba(models.Model):

    id_adresu = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255)
    telefon = models.CharField(max_length=20)
    osoba = models.ForeignKey(Osoba, on_delete=models.CASCADE)
    czy_domyslny = models.BooleanField(default=False)


class TypZdarzenia(models.Model):

    id_typu = models.AutoField(primary_key=True)
    nazwa_zdarzenia = models.CharField(max_length=45)

    # Methods
    def __str__(self):
        return self.nazwa_zdarzenia


class Zdarzenie(models.Model):

    id_zdarzenia = models.AutoField(primary_key=True)
    data_zdarzenia = models.DateTimeField(auto_now=False, auto_now_add=False)
    temat = models.CharField(max_length=255)
    typ = models.ForeignKey(TypZdarzenia, on_delete=models.PROTECT)
    uzytkownik = models.ForeignKey(Profil, on_delete=models.PROTECT)
    kontrahent = models.ForeignKey(Kontrahent, on_delete=models.PROTECT)
    notatka = models.TextField()


class StatusOferty(models.Model):

    id_statusu_oferty = models.AutoField(primary_key=True)
    nazwa_statusu = models.CharField(max_length=45)

    def __str__(self):
        return self.nazwa_statusu


class Oferta(models.Model):

    id_oferty = models.AutoField(primary_key=True)
    temat = models.CharField(max_length=255)
    produkt = models.CharField(max_length=255)
    kontrahent = models.ForeignKey(Kontrahent, on_delete=models.PROTECT, db_column="kontrahent")
    termin_waznosci = models.DateField(auto_now=False, auto_now_add=False, verbose_name='Termin ważności')
    wartosc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Wartość')
    status = models.ForeignKey(StatusOferty, null=True, on_delete=models.SET_NULL)
    akceptacja = models.BooleanField(default=False)
    data_sporzadzenia = models.DateField(auto_now=False, auto_now_add=False, verbose_name='Data sporządzenia')
    waluta = models.CharField(max_length=3, default='PLN')
    opiekun = models.ForeignKey(Profil, null=True, blank=True, on_delete=models.PROTECT)
    oferta_rodzic = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT)

    # prawdopodobnie do usunięcia
    @property
    def is_owner_of(self, profil):
        return True if self.opiekun == profil else False


class StatusUmowy(models.Model):

    id_statusu = models.AutoField(primary_key=True)
    nazwa = models.CharField(max_length=45)

    # Methods
    def __str__(self):
        return self.nazwa


class Umowa(models.Model):
    id_umowy = models.AutoField(primary_key=True)
    temat = models.CharField(max_length=255)
    produkt = models.CharField(max_length=255)
    termin_waznosci = models.DateField(null=True, auto_now=False, auto_now_add=False, verbose_name='Termin ważności')
    data_platnosci = models.DateField(null=True, auto_now=False, auto_now_add=False, verbose_name='Data płatności')
    data_sporzadzenia = models.DateField(auto_now=False, auto_now_add=False, verbose_name='Data sporządzenia')
    termin_platnosci = models.IntegerField(verbose_name='Termin płatności')
    waluta = models.CharField(max_length=3)
    kontrahent = models.ForeignKey(Kontrahent, on_delete=models.PROTECT)
    status = models.ForeignKey(StatusUmowy, null=True, on_delete=models.SET_NULL)
    wartosc = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Wartość')
    opiekun = models.ForeignKey(Profil, null=True, blank=True, on_delete=models.PROTECT)

    def how_much_progress(self):
        pass

    def __str__(self):
        return ' Do: ' + self.termin_waznosci.strftime('%m/%d/%Y') + ', ' + self.temat


def set_upload_path(instance, filename):
    rok = date.today().year
    miesiac = date.today().month
    if instance.umowa is not None:
        return 'umowy/{0}/{1}/{2}'.format(rok, miesiac, filename)
    elif instance.oferta is not None:
        return 'oferty/{0}/{1}/{2}'.format(rok, miesiac, filename)


class Dokument(models.Model):

    prefix = ''
    id_dokumentu = models.AutoField(primary_key=True)
    tytul_dokumentu = models.CharField(max_length=255, verbose_name='Tytuł dokumentu')
    nazwa_pliku = models.FileField(max_length=255, upload_to=set_upload_path)
    data_dodania = models.DateTimeField(auto_now=False, auto_now_add=True)
    umowa = models.ForeignKey(Umowa, null=True, on_delete=models.PROTECT)
    oferta = models.ForeignKey(Oferta, null=True, on_delete=models.PROTECT)
    uzytkownik = models.ForeignKey(Profil, on_delete=models.PROTECT)


@receiver(models.signals.post_delete, sender=Dokument)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Usuwa pliki z systemu plików gdy obiekt Dokument jest usuwany
    """
    if instance.nazwa_pliku:
        if os.path.isfile(instance.nazwa_pliku.path):
            os.remove(instance.nazwa_pliku.path)


class Platnosc(models.Model):

    id_platnosci = models.AutoField(primary_key=True)
    termin = models.DateField(auto_now=False, auto_now_add=False)
    kwota = models.DecimalField(max_digits=10, decimal_places=2)
    umowa = models.ForeignKey(Umowa, on_delete=models.PROTECT)
    kwota_zaksiegowana = models.DecimalField(max_digits=10, decimal_places=2)

    def is_done(self):
        return not self.kwota > self.kwota_zaksiegowana

    def is_delayed(self):
        return date.today() > self.termin and self.kwota > self.kwota_zaksiegowana

    def how_many_days_left(self):
        time_delta = self.termin - date.today()
        return ('{value} {end}'.format(value=time_delta.days, end='dni'))

    def __str__(self):
        return 'Platność dla: ' + self.umowa.kontrahent.nazwa_krotka + \
               ', o wartości: ' + str(self.kwota) + str(self.umowa.waluta) + \
               ', płatna do: ' + str(self.termin)


class AdresatNadawca(models.Model):

    id_adresata_nadawcy = models.AutoField(primary_key=True)
    nazwa = models.CharField(max_length=255, unique=True)
    miasto = models.CharField(max_length=255)
    kod_pocztowy = models.CharField(max_length=6)
    ulica = models.CharField(max_length=255)

    def __str__(self):
        return self.nazwa

    def get_absolute_url(self):
        return reverse('korespondencja:kontakt-list')


class Korespondencja(models.Model):
    RODZAJ = (('Wychodząca', 'Wychodząca'), ('Przychodząca', 'Przychodząca'))

    id_korespondencji = models.AutoField(primary_key=True)
    numer_korespondencji = models.CharField(max_length=60, null=True, blank=True)
    temat = models.CharField(max_length=255)
    data_dodania = models.DateTimeField(auto_now=False, auto_now_add=True)
    data_przyjscia_wyjscia = models.DateField(auto_now=False, auto_now_add=False)
    rodzaj = models.CharField(max_length=255, choices=RODZAJ, default=RODZAJ[1])
    uzytkownik = models.ForeignKey(Profil, on_delete=models.PROTECT)
    adresat_nadawca = models.ForeignKey(AdresatNadawca, on_delete=models.CASCADE)

    def get_absolute_url(self):
        return HttpResponseRedirect('korespondencja:korespondencja-list')

    def __str__(self):
        return self.temat


def post_save_korespondencja(sender, instance, *args, **kwargs):
    if not instance.numer_korespondencji:
        if instance.rodzaj == 'Przychodząca':
            rodzaj = 'P'
        else:
            rodzaj = 'W'
        today = date.today()
        pk = instance.pk
        instance.numer_korespondencji = rodzaj + str(pk) + '/' + today.strftime("%Y/%m/%d")
        instance.save()


post_save.connect(post_save_korespondencja, sender=Korespondencja)


class PlikKorespondencji(models.Model):
    id_pliku_korespondencji = models.AutoField(primary_key=True)
    nazwa_pliku = models.CharField(max_length=255)
    sciezka_do_pliku = models.CharField(max_length=255)
    korespondencja = models.ForeignKey(Korespondencja, on_delete=models.CASCADE)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profil.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profil.save()
