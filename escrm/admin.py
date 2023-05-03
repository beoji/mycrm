# Register your models here.
from django.contrib import admin
from .models import Profil, Oferta, StatusOferty, Platnosc, TypAdresu, TypZdarzenia
from .models import Kontrahent, Osoba, AdresKontrahent, AdresOsoba, AdresatNadawca, Korespondencja, Umowa, StatusUmowy


class ProfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefon', 'stanowisko']


admin.site.register(Kontrahent)
admin.site.register(AdresKontrahent)
admin.site.register(Osoba)
admin.site.register(AdresOsoba)
admin.site.register(AdresatNadawca)
admin.site.register(Korespondencja)
admin.site.register(Profil, ProfilAdmin)
admin.site.register(Umowa)
admin.site.register(StatusUmowy)
admin.site.register(Oferta)
admin.site.register(StatusOferty)
admin.site.register(Platnosc)
admin.site.register(TypAdresu)
admin.site.register(TypZdarzenia)

