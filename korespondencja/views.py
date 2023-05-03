from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from escrm.models import Korespondencja, AdresatNadawca, Kontrahent
from django.urls import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from .forms import KorespondencjaForm, AdresatNadawcaForm
from django.core.serializers import serialize


# - KORESPONDENCJA


class KorespondencjaList(LoginRequiredMixin, generic.ListView):
    model = Korespondencja
    template_name = 'korespondencja/korespondencja_list.html'


class KorespondencjaDetail(LoginRequiredMixin, generic.DetailView):
    model = Korespondencja
    template_name = 'korespondencja/korespondencja_detail.html'


class KorespondencjaCreate(LoginRequiredMixin, generic.View):
    template = 'korespondencja/korespondencja_form.html'
    context = dict()

    def get(self, request):
        form_co = KorespondencjaForm()  # Formularz docelowy korespondencji
        form_adres = AdresatNadawcaForm()  # Formularz pomocniczy adresu
        # Inicjalizacja pola 'rodzaj' formularza odpowiednią wartością
        rodzaj = request.GET.get('rodzaj')
        if rodzaj == 'p':
            form_co.initial['rodzaj'] = 'Przychodząca'
        if rodzaj == 'w':
            form_co.initial['rodzaj'] = 'Wychodząca'
        # Dodanie formularzy do contextu
        self.context['form_co'] = form_co
        self.context['form_adres'] = form_adres
        self.context['kontrahent_list'] = Kontrahent.objects.all()
        return render(request, self.template, self.context)

    def post(self, request):
        form_co = KorespondencjaForm(request.POST)
        form_adres = AdresatNadawcaForm(request.POST)

        if form_co.is_valid():
            nazwa_kontaktu = form_adres['nazwa'].value()
            if AdresatNadawca.objects.filter(nazwa=nazwa_kontaktu):
                kontakt = AdresatNadawca.objects.get(nazwa=nazwa_kontaktu)
            else:
                if form_adres.is_valid():
                    kontakt = form_adres.save()
                else:
                    self.context['form_co'] = form_co
                    self.context['form_adres'] = form_adres
                    return render(request, self.template, self.context)

            temat = form_co.cleaned_data.get('temat')
            data = form_co.cleaned_data.get('data_przyjscia_wyjscia')
            rodzaj = form_co.cleaned_data.get('rodzaj')
            Korespondencja.objects.create(temat=temat,
                                          data_przyjscia_wyjscia=data,
                                          rodzaj=rodzaj,
                                          uzytkownik=request.user.profil,
                                          adresat_nadawca=kontakt)
            is_next = request.POST.get('is_next')
            if is_next == 'yes':
                if rodzaj == 'Przychodząca':
                    url = "%s?rodzaj=p" % reverse('korespondencja:korespondencja-create')
                else:
                    url = "%s?rodzaj=w" % reverse('korespondencja:korespondencja-create')
                return HttpResponseRedirect(url)
            return HttpResponseRedirect(reverse('korespondencja:korespondencja-list'))

        self.context['form_co'] = form_co
        self.context['form_adres'] = form_adres
        return render(request, self.template, self.context)


class KorespondencjaUpdate(LoginRequiredMixin, generic.View):
    template = 'korespondencja/korespondencja_form.html'
    context = dict()

    def get(self, request, **kwargs):
        pk = kwargs.get('pk')
        obj = Korespondencja.objects.get(pk=pk)
        adr = obj.adresat_nadawca
        form_co = KorespondencjaForm(instance=obj)  # Formularz docelowy korespondencji
        form_adres = AdresatNadawcaForm(instance=adr)  # Formularz pomocniczy adresu
        self.context['form_co'] = form_co
        self.context['form_adres'] = form_adres
        return render(request, self.template, self.context)

    def post(self, request, **kwargs):
        pk = kwargs.get('pk')
        form_co = KorespondencjaForm(request.POST)
        form_adres = AdresatNadawcaForm(request.POST)

        if form_co.is_valid():
            nazwa_kontaktu = form_adres['nazwa'].value()
            if AdresatNadawca.objects.filter(nazwa=nazwa_kontaktu):
                kontakt = AdresatNadawca.objects.get(nazwa=nazwa_kontaktu)
            else:
                if form_adres.is_valid():
                    kontakt = form_adres.save()
                else:
                    self.context['form_co'] = form_co
                    self.context['form_adres'] = form_adres
                    return render(request, self.template, self.context)

            obj = Korespondencja.objects.get(pk=pk)
            obj.temat = form_co.cleaned_data.get('temat')
            obj.data_przyjscia_wyjscia = form_co.cleaned_data.get('data_przyjscia_wyjscia')
            obj.rodzaj = form_co.cleaned_data.get('rodzaj')
            obj.adresat_nadawca = kontakt
            obj.save()
            return HttpResponseRedirect(reverse('korespondencja:korespondencja-list'))

        self.context['form_co'] = form_co
        self.context['form_adres'] = form_adres
        return render(request, self.template, self.context)


class KorespondencjaDelete(LoginRequiredMixin, generic.DeleteView):
    model = Korespondencja

    def get_success_url(self):
        return reverse('korespondencja:korespondencja-list')


# Ajax request na potrzeby auto-uzupelniania adresata_nadawcy
def personhelper(request):
    if request.method == 'GET':
        name = request.GET.get('input')
        results = AdresatNadawca.objects.filter(nazwa__icontains=name)
        return JsonResponse({'results': serialize('json', results)})


# Ajax request na potrzeby filtrowania kolumny adresaci/nadawcy
def getrecievers(request):
    if request.method == 'GET':
        results = AdresatNadawca.objects.all()
        return JsonResponse({'results': serialize('json', results)})


def get_mail_by_date(request):
    if request.method == 'GET':
        queryset = Korespondencja.objects.all()
        if 'date_from' in request.GET:
            date_from = request.GET.get('date_from')
            if date_from != 'null' and date_from != '':
                queryset = queryset.filter(data_przyjscia_wyjscia__gte=date_from)
        if 'date_to' in request.GET and 'date_to' != 'null' and 'date_to' != '':
            date_to = request.GET.get('date_to')
            if date_to != 'null' and date_to != '':
                queryset = queryset.filter(data_przyjscia_wyjscia__lte=date_to)
        table_html = render_to_string('snippets/korespondencja_table.html',
                                        {'korespondencja_list': queryset})
        return JsonResponse({'results': table_html})


# Adresat/Nadawca


class KontaktList(LoginRequiredMixin, generic.ListView):
    template_name = 'korespondencja/adresatnadawca_list.html'
    model = AdresatNadawca
    context_object_name = 'kontakt_list'


class KontaktDetail(LoginRequiredMixin, generic.DetailView):
    template_name = 'korespondencja/adresatnadawca_detail.html'
    model = AdresatNadawca
    context_object_name = 'kontakt'


class KontaktUpdate(LoginRequiredMixin, generic.UpdateView):
    template_name = 'korespondencja/adresatnadawca_form.html'
    form_class = AdresatNadawcaForm
    model = AdresatNadawca


class KontaktDelete(LoginRequiredMixin, generic.DeleteView):
    model = Korespondencja

    def get_success_url(self):
        return reverse('korespondencja:kontakt-list')



