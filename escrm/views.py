from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.forms import HiddenInput, ModelChoiceField, CharField
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views import generic
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, render
from .forms import OsobaForm, AdresOsobaForm, KontrahentForm, AdresKontrahentForm, AdresKontrahentFormNew, OfertaForm
from .forms import OfertaEditForm, ZdarzenieForm, DokumentForm
from .forms import UmowaForm, PlatnoscForm
from django.db.models import ProtectedError
from .models import Profil, Oferta, Platnosc
from .models import Kontrahent, Osoba, Umowa, Dokument
from .models import Zdarzenie, TypZdarzenia, AdresKontrahent, AdresOsoba
from math import ceil
import datetime
from django.utils import timezone
import calendar
from django.http import StreamingHttpResponse
import os
import mimetypes


class CrmDashboard(LoginRequiredMixin, generic.TemplateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    template_name = 'escrm/dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super(CrmDashboard, self).get_context_data(**kwargs)
        context['lista_kontrahentow'] = Kontrahent.objects.filter(opiekun=self.request.user.profil)[:5]
        context['lista_umow'] = Umowa.objects.filter(opiekun=self.request.user.profil)[:5]
        context['lista_ofert'] = Oferta.objects.filter(opiekun=self.request.user.profil)[:5]
        context['lista_zdarzen'] = Zdarzenie.objects.filter(uzytkownik=self.request.user.profil)[:5]
        return context


# KONTRAHENT -


class KontrahentList(LoginRequiredMixin, generic.ListView):
    model = Kontrahent
    context_object_name = 'lista_kontrahentow'

    def get_queryset(self):
        return Kontrahent.objects.order_by('-id_kontrahenta')


class KontrahentDetail(LoginRequiredMixin, generic.DetailView):
    model = Kontrahent

    def get_context_data(self, **kwargs):
        ctx = super(KontrahentDetail, self).get_context_data(**kwargs)
        ctx['form_adres'] = AdresKontrahentFormNew(initial={'kontrahent': self.object, 'czy_domyslny': False, })
        ctx['form_osoba'] = OsobaForm(initial={'kontrahent': self.object, })
        ctx['form_osoba_adres'] = AdresOsobaForm(initial={'czy_domyslny': True, })
        ctx['next'] = self.request.META.get('HTTP_REFERER')
        return ctx


class KontrahentCreate(LoginRequiredMixin, generic.View):
    template = 'escrm/kontrahent_form.html'
    ctx = dict()
    message = "Utworzono pomyślnie nowego kontrahenta"

    def get(self, request):
        self.ctx['form_kontrahent'] = KontrahentForm(initial={'czy_aktywny': True})

        if request.user.groups.filter(name__in=["szef_dzialu_sprzedazy", "prezes"]).exists() or request.user.is_staff:
            self.ctx['form_kontrahent'].fields['opiekun'] = ModelChoiceField(queryset=Profil.objects.all())
        elif request.user.groups.filter(name="opiekun_klienta").exists():
            self.ctx['form_kontrahent'].fields['opiekun'] = ModelChoiceField(
                queryset=Profil.objects.all().filter(id=request.user.profil.id))

        self.ctx['form_kontrahent'].fields['opiekun'].required = False
        self.ctx['form_kontrahent'].fields['czy_aktywny'].widget = HiddenInput()
        self.ctx['form_adres'] = AdresKontrahentForm(initial={'typ_adresu': 1})
        self.ctx['title'] = 'Dodaj nowego kontrahenta'
        self.ctx['next'] = self.request.META.get('HTTP_REFERER')
        # print(self.request.META.get('HTTP_REFERER'))
        return render(request, self.template, self.ctx)

    def post(self, request):
        kontrahent_form = KontrahentForm(request.POST)
        adres_form = AdresKontrahentForm(request.POST)
        """if kontrahent_form.is_valid():
            kontrahent = kontrahent_form.save()
        else:
            self.ctx['form_kontrahent'] = kontrahent_form
            self.ctx['form_adres'] = adres_form
            return render(request, self.template, self.ctx)"""
        if kontrahent_form.is_valid() and adres_form.is_valid():
            kontrahent = kontrahent_form.save()
            adres = adres_form.save(commit=False)
            adres.kontrahent = kontrahent
            adres.czy_domyslny = True
            adres.save()
            messages.success(self.request, self.message)
            return HttpResponseRedirect(reverse_lazy('escrm:kontrahent-detail', kwargs={'pk': kontrahent.pk}))
        else:
            self.ctx['form_kontrahent'] = kontrahent_form
            self.ctx['form_adres'] = adres_form
            return render(request, self.template, self.ctx)


class KontrahentUpdate(LoginRequiredMixin, generic.UpdateView):
    template_name = 'escrm/kontrahent_form_edit.html'
    model = Kontrahent
    fields = ['nazwa_krotka', 'nazwa_dluga', 'nip', 'telefon', 'email']

    def get_queryset(self):
        if self.request.user.groups.filter(name__in=["szef_dzialu_sprzedazy", "prezes"]).exists() or self.request.user.is_staff:
            self.fields.append('opiekun')
        return Kontrahent.objects.filter(pk=self.kwargs.get('pk'))


class KontrahentDelete(LoginRequiredMixin, generic.DeleteView):
    model = Kontrahent
    success_message = 'Kontrahent został pomyślnie usunięty.'
    protected_message = 'Kontrahent nie może zostać usunięty, ponieważ istnieją osoby z nim powiązane.'
    success_url = '/escrm/kontrahent/'

    def delete(self, request, *args, **kwargs):
        try:
            delete = super(KontrahentDelete, self).delete(request, *args, **kwargs)
            messages.success(self.request, self.success_message)
            return delete
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return HttpResponseRedirect(reverse_lazy('escrm:kontrahent-detail', kwargs={'pk': self.object.pk}))


@login_required
def kontrahent_dashboard(request, pk):
    kontrahent = Kontrahent.objects.get(pk=pk)

    if request.user.profil == kontrahent.opiekun:
        context = dict(kontrahent=kontrahent)
        context['oferty'] = kontrahent.get_last_oferty(5)
        context['zdarzenia'] = kontrahent.zdarzenie_set.all()[:5]
        context['umowy'] = kontrahent.umowa_set.all()[:5]
        return render(request, 'escrm/kontrahent_dashboard.html', context)
    else:
        message = "Brak uprawnień do widoku CRM tego kontrahenta"
        messages.error(request, message)
        return HttpResponseRedirect(reverse_lazy('escrm:kontrahent-list'))


@login_required
def kontrahent_take(request, pk):
    """ dodanie opiekuna do kontrahenta """
    # mimo, że w widoku opcja umożliwiająca wybranie siebie opiekunem nie beędzie widoczna jeżeli brak uprawnień lub
    # opiekun już przypisany (chyba, że ES zdecyduje inaczej) to tutaj również należy sprawdzić wszystkie konieczne
    # warunki

    # 1. użytkownik zalogowany
    # 2. użytkownik posiada odpowiednią rolę lub uprawnienie (trzeba się nad tym zastanowić)
    # 3. kontrahent nie ma jeszcze opiekuna
    kontrahent = Kontrahent.objects.get(pk=pk)

    if kontrahent.opiekun is None:
        kontrahent.opiekun = Profil.objects.get(user=request.user)
        kontrahent.save()
        return HttpResponseRedirect(reverse_lazy('escrm:kontrahent-detail', kwargs={'pk': pk}))
    else:
        message = "Kontrahent ma już przypisanego opiekuna"
        messages.error(request, message)
        return HttpResponseRedirect(reverse_lazy('escrm:kontrahent-list'))

# ADRES_KONTRAHENT -


def default_check(request, pk):
    """AJAX post adres-kontrahent-czy-domyslny field"""
    try:
        adres = AdresKontrahent.objects.get(pk=pk)
        adres.czy_domyslny = True
        adres.save()
        nowy_adres = adres.ulica + ', ' + adres.kod_pocztowy + ', ' + adres.miasto
        return JsonResponse({'result': 'done',
                             'nowy_adres': nowy_adres})
    except AdresKontrahent.DoesNotExist:
        return HttpResponse('Ooops! Something gone wrong...')


def adres_kontrahent_create(request):
    """AJAX post adres-kontrahent create form"""
    data = dict()
    if request.method == 'POST':
        nowy_adres = AdresKontrahentFormNew(request.POST)
        if nowy_adres.is_valid():
            nowy_adres.save()
            list_modal = render_to_string('escrm/adresy/kontrahentadres_list_modal.html',
                                         {'object': nowy_adres.cleaned_data.get('kontrahent')})
            brand_new_form = render_to_string('escrm/adresy/kontrahentadres_form_modal.html',
                                             {'form_adres': AdresKontrahentFormNew()})
            data['list_modal'] = list_modal
            data['is_valid'] = 'True'
            data['new_form'] = brand_new_form
        else:
            invalid_form = render_to_string('escrm/adresy/kontrahentadres_form_modal.html',
                                           {'form_adres': nowy_adres})
            data['is_valid'] = 'False'
            data['invalid_form'] = invalid_form
        return JsonResponse(data)


def adres_kontrahent_update(request):
    """AJAX get adres-kontrahent update form"""
    data = dict()
    if request.method == 'GET':
        pk = request.GET.get('pk')
        if AdresKontrahent.objects.filter(pk=pk):
            adres = AdresKontrahent.objects.get(pk=pk)
            adres_bounded = AdresKontrahentFormNew(instance=adres)
            rendered = render_to_string('escrm/adresy/kontrahentadres_form_modal.html',
                                        {'form_adres': adres_bounded, 'role': 'update', 'pk': adres.pk, },)
            data['result'] = 'success'
            data['modal'] = rendered
        else:
            data['result'] = 'failed'
        return JsonResponse(data)


def adres_kontrahent_update_saving(request, pk):
    """AJAX post adres-kontrahent update form"""
    data = dict()
    if request.method == 'POST':
        adres = get_object_or_404(AdresKontrahent, pk=pk)
        adres_to_save = AdresKontrahentFormNew(request.POST, instance=adres)
        if adres_to_save.is_valid():
            adres_to_save.save()
            list_modal = render_to_string('escrm/adresy/kontrahentadres_list_modal.html',
                                       {'object': adres_to_save.cleaned_data.get('kontrahent')},)
            data['is_valid'] = 'True'
            data['list_modal'] = list_modal
        else:
            invalid_form = render_to_string('escrm/adresy/kontrahentadres_form_modal.html',
                                           {'form_adres': adres_to_save, 'role': 'update', 'pk': adres.pk,})
            data['is_valid'] = 'False'
            data['invalid_form'] = invalid_form
        return JsonResponse(data)


def adres_kontrahent_delete(request, pk):
    """AJAX post adres-kontrahent delete form"""
    data = dict()
    if request.method == 'POST':
        if AdresKontrahent.objects.filter(pk=pk):
            adres = AdresKontrahent.objects.get(pk=pk)
            if not adres.czy_domyslny:
                adres.delete()
                data['result'] = 'success'
            else:
                data['result'] = 'domyslny'
        else:
            data['result'] = 'failed'
        return JsonResponse(data)


# OSOBA -


class OsobaDetail(LoginRequiredMixin, generic.DetailView):
    model = Osoba

    def get_context_data(self, **kwargs):
        ctx = super(OsobaDetail, self).get_context_data(**kwargs)
        ctx['form'] = AdresOsobaForm()
        return ctx


def osoba_create(request):
    """AJAX post request Osoba create form"""
    print(request.POST)
    osoba = OsobaForm(request.POST)
    adres = AdresOsobaForm(request.POST)
    ctx = dict()
    kontrahent_pk = request.POST.get('kontrahent')
    kontrahent = Kontrahent.objects.get(pk=kontrahent_pk)
    if osoba.is_valid() and adres.is_valid():
        obj = osoba.save()
        obj.kontrahent.add(kontrahent)
        obj.save()
        adr = adres.save(commit=False)
        adr.osoba = obj
        adr.czy_domyslny = True
        adr.save()
        ctx['is_valid'] = 'True'
        ctx['table'] = render_to_string('escrm/osoby/osoba_table.html', {'kontrahent': kontrahent}, request=request)
        ctx['new_modal'] = render_to_string('escrm/osoby/osoba_form_create_modal.html',
                                           {'form_osoba': OsobaForm(),
                                            'form_osoba_adres': AdresOsobaForm(), 'object': kontrahent })
    else:
        invalid_form = render_to_string('escrm/osoby/osoba_form_create_modal.html',
                                        {'form_osoba': osoba,
                                         'form_osoba_adres': adres, 'object': kontrahent })
        ctx['is_valid'] = 'False'
        ctx['invalid_form'] = invalid_form
    return JsonResponse(ctx)


def osoba_update(request):
    """AJAX get request Osoba bounded form"""
    ctx = dict()
    if request.method == 'GET':
        if request.GET.get('pk'):
            pk = request.GET.get('pk')
            if Osoba.objects.filter(pk=pk):
                osoba = Osoba.objects.get(pk=pk)
                form = OsobaForm(instance=osoba)
                ctx['modal'] = render_to_string('escrm/osoby/osoba_form_update_modal.html',
                                                {'form': form, 'pk': pk, })
    return JsonResponse(ctx)


def osoba_update_saving(request, pk):
    """AJAX post request Osoba save form"""
    data = dict()
    if request.method == 'POST':
        osoba = get_object_or_404(Osoba, pk=pk)
        osoba_to_save = OsobaForm(request.POST, instance=osoba)
        if osoba_to_save.is_valid():
            osoba_to_save.save()
            if 'kontrahent' in request.POST:
                kontrahent_id = request.POST.get('kontrahent')
                print(kontrahent_id)
                kontrahent = Kontrahent.objects.get(pk=kontrahent_id)
                rendered_table = render_to_string('escrm/osoby/osoba_table.html',
                                                {'kontrahent': kontrahent,}, request=request)
                data['table'] = rendered_table
            detail_content = render_to_string('escrm/osoby/osoba_detail_content_render.html',
                                              {'osoba': osoba,})
            data['detail'] = detail_content
            data['is_valid'] = 'True'
        else:
            data['invalid_form'] = render_to_string('escrm/osoby/osoba_form_update_modal.html',
                                                    {'form': osoba_to_save, 'pk': pk, })
            data['is_valid'] = 'False'
        return JsonResponse(data)


class OsobaDelete(LoginRequiredMixin, generic.DeleteView):
    model = Osoba
    success_message = 'Osoba została pomyślnie usunięta.'

    def get_success_url(self):
        first_kontrahent = self.object.kontrahent.all()[0].pk
        return reverse_lazy('escrm:kontrahent-detail', kwargs={'pk': first_kontrahent})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(OsobaDelete, self).delete(request, *args, **kwargs)

# ADRES_OSOBA


def adres_osoba_create(request):
    ctx = dict()
    if request.method == 'POST':
        adres = AdresOsobaForm(request.POST)
        if adres.is_valid():
            adr = adres.save(commit=False)
            osoba_pk = request.POST.get('osoba')
            osoba = Osoba.objects.get(pk=osoba_pk)
            adr.osoba = osoba
            adr.save()
            table = render_to_string('escrm/adresy/osobaadres_table.html', {'osoba': osoba})
            ctx['table'] = table
            ctx['new_form'] = render_to_string('escrm/adresy/osobaadres_form_modal.html', {'form': AdresOsobaForm()})
            ctx['is_valid'] = 'True'
        else:
            ctx['invalid_form'] = render_to_string('escrm/adresy/osobaadres_form_modal.html', {'form': adres})
            ctx['is_valid'] = 'False'
        return JsonResponse(ctx)


def adres_osoba_delete(request, pk):
    ctx = dict()
    if request.method == 'POST':
        try:
            adres = AdresOsoba.objects.get(pk=pk)
            if adres.czy_domyslny:
                ctx['result'] = 'domyslny'
                return JsonResponse(ctx)
            adres.delete()
            ctx['result'] = 'success'
        except AdresOsoba.DoesNotExist:
            ctx['result'] = 'failed'
        return JsonResponse(ctx)


def adres_osoba_update(request):
    """AJAX get request AdresOsoba bounded form"""
    ctx = dict()
    if request.method == 'GET':
        if request.GET.get('pk'):
            pk = request.GET.get('pk')
            if AdresOsoba.objects.filter(pk=pk):
                adres = AdresOsoba.objects.get(pk=pk)
                form = AdresOsobaForm(instance=adres)
                ctx['modal'] = render_to_string('escrm/adresy/osobaadres_form_modal.html',
                                                context={'form': form, 'object': adres, 'role': 'update'}, request=request)
    return JsonResponse(ctx)


def adres_osoba_update_saving(request, pk):
    """AJAX post request Osoba save form"""
    data = dict()
    if request.method == 'POST':
        adres = get_object_or_404(AdresOsoba, pk=pk)
        adres_to_save = AdresOsobaForm(request.POST, instance=adres)
        if adres_to_save.is_valid():
            adr = adres_to_save.save()
            table = render_to_string('escrm/adresy/osobaadres_table.html',
                                    {'osoba': adr.osoba})
            data['table'] = table
            data['is_valid'] = 'True'
        else:
            data['invalid_form'] = render_to_string('escrm/adresy/osobaadres_form_modal.html',
                                                    {'form': adres_to_save, 'object': adres, 'role': 'update'}, request=request)
            data['is_valid'] = 'False'
        return JsonResponse(data)


# PRODUKTY -


class ProduktyList(LoginRequiredMixin, generic.TemplateView):
    template_name = 'escrm/produkty_list.html'

    def get_context_data(self, **kwargs):
        context = super(ProduktyList, self).get_context_data(**kwargs)
        #umowy = Umowa.objects.order_by('-data_sporzadzenia')
        oferty = Oferta.objects.order_by('-data_sporzadzenia')
        context['lista_produktow'] = oferty
        return context

# DOKUMENTY


# def respond_as_attachment(request, file_path, original_filename):
#     print('path ' + file_path)
#     print('original_filename: ' + original_filename)
#     fp = open(file_path, 'rb')
#     response = HttpResponse(fp.read())
#     fp.close()
#     type, encoding = mimetypes.guess_type(original_filename)
#     if type is None:
#         type = 'application/octet-stream'
#     response['Content-Type'] = type
#     response['Content-Length'] = str(os.stat(file_path).st_size)
#     if encoding is not None:
#         response['Content-Encoding'] = encoding
#
#     # To inspect details for the below code, see http://greenbytes.de/tech/tc2231/
#     if u'WebKit' in request.META['HTTP_USER_AGENT']:
#         # Safari 3.0 and Chrome 2.0 accepts UTF-8 encoded string directly.
#         filename_header = 'filename=%s' % original_filename.encode('utf-8')
#     elif u'MSIE' in request.META['HTTP_USER_AGENT']:
#         # IE does not support internationalized filename at all.
#         # It can only recognize internationalized URL, so we do the trick via routing rules.
#         filename_header = ''
#     else:
#         # For others like Firefox, we follow RFC2231 (encoding extension in HTTP headers).
#         filename_header = 'filename=%s' % urllib.quote(original_filename.encode('utf-8'))
#         filename_header += 'filename*=UTF-8\'\'%s' % urllib.quote(original_filename.encode('utf-8'))
#     response['Content-Disposition'] = 'attachment; ' + filename_header
#     return response


@login_required
def serve_using_django_in_chunks(request, filename):

    # file_full_path = settings.MEDIA_URL + filename
    if not os.path.isfile(filename):
        messages.error(request, 'Podany plik nie istnieje')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    file_full_path = filename
    filename = filename.split('\\')[-1]
    response = StreamingHttpResponse((line for line in open(file_full_path, 'rb')))
    mime_type, encoding = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    response['Content-Type'] = mime_type
    if encoding is not None:
            response['Content-Encoding'] = encoding

    response['Content-Disposition'] = "attachment; filename={0}".format(filename)
    response['Content-Length'] = os.path.getsize(file_full_path)
    return response


@login_required
def dokument_get(request, pk):
    dokument = get_object_or_404(Dokument, pk=pk)
    return serve_using_django_in_chunks(request, dokument.nazwa_pliku.path)

    # filename = dokument.nazwa_pliku.path.split('\\')[-1]
    # return respond_as_attachment(request, dokument.nazwa_pliku.path, filename)


class DokumentDelete(LoginRequiredMixin, generic.DeleteView):
    model = Dokument
    success_message = 'Dokument został usunięty.'

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(DokumentDelete, self).delete(request, *args, **kwargs)


@login_required
def dokument_add(request, pk):
    dokument_form = DokumentForm(request.POST, request.FILES)

    # print(request.POST)
    # print(request.FILES)
    # print(dokument_form.errors)
    typ = request.POST.get('typ')
    context = dict()

    if dokument_form.is_valid():
        dokument_form.instance.uzytkownik = request.user.profil
        print("form valid")
        if typ == 'oferta':
            print("to jest oferta")
            oferta = get_object_or_404(Oferta, pk=pk)
            dokument_form.instance.oferta = oferta
            dokument_form.save()
            messages.success(request, 'Plik został dodany do oferty')
            # return reverse_lazy('escrm:oferta-detail', kwargs={'pk': pk, 'pk_oferty': oferta.kontrahent.id_kontrahenta})
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        elif typ == 'umowa':
            umowa = get_object_or_404(Umowa, pk=pk)
            dokument_form.instance.umowa = umowa
            dokument_form.save()
            messages.success(request, 'Plik został dodany do umowy')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, 'Nieprawidłowy typ obiektu dla dodawanego pliku')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        print("form not valid")
        context['is_valid'] = 'False'
        return JsonResponse(context)


# OFERTY


class OfertaCreate(LoginRequiredMixin, generic.CreateView):
    model = Oferta
    form_class = OfertaForm
    form_dokument = DokumentForm()
    # context = dict()
    message = "Oferta została utworzona"

    def post(self, request, *args, **kwargs):
        form_oferta = OfertaForm(request.POST)
        form_dokument = DokumentForm(request.POST, request.FILES)
        file = request.FILES['nazwa_pliku']

        if file:
            if form_oferta.is_valid() and form_dokument.is_valid():
                # for f in files:

                form_dokument.instance.uzytkownik = self.request.user.profil
                form_oferta.instance.opiekun = self.request.user.profil
                form_oferta.instance.data_dodania = timezone.now()
                oferta = form_oferta.save()
                form_dokument.instance.oferta = oferta
                form_dokument.save()
                messages.success(self.request, self.message)
                return HttpResponseRedirect(reverse_lazy('escrm:kontrahent-oferty', kwargs={'pk': oferta.kontrahent.pk}))
            else:
                return render(request, self.template, self.get_context_data())
        else:
            if form_oferta.is_valid():
                form_oferta.instance.opiekun = self.request.user.profil
                oferta = form_oferta.save()
                messages.success(self.request, self.message)
                return HttpResponseRedirect(reverse_lazy('escrm:kontrahent-oferty', kwargs={'pk': oferta.kontrahent.pk}))
            else:
                return render(request, self.template, self.get_context_data())

    def get_initial(self):
        initial = super(OfertaCreate, self).get_initial()
        self.kontrahent = get_object_or_404(Kontrahent, id_kontrahenta=self.kwargs.get('pk'))
        initial['kontrahent'] = self.kontrahent
        return initial

    def get_context_data(self, **kwargs):
        context = super(OfertaCreate, self).get_context_data(**kwargs)
        context['kontrahent'] = self.kontrahent
        context['form_dokument'] = self.form_dokument
        # context['form_dokument'].fields['nazwa_pliku'].upload_to = 'oferty/%Y/%m/'
        context['form_dokument'].fields['nazwa_pliku'].required = False
        context['form_dokument'].fields['tytul_dokumentu'].required = False
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context

    def get_success_url(self):
        return reverse_lazy('escrm:kontrahent-oferty', kwargs={'pk': self.kwargs.get('pk')})


class OfertaDetail(LoginRequiredMixin, generic.DetailView):
    model = Oferta
    form_dokument = DokumentForm()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_dokument'] = self.form_dokument
        context['form_dokument'].fields['nazwa_pliku'].required = False
        context['form_dokument'].fields['tytul_dokumentu'].required = False
        context['form_dokument'].fields['typ'] = CharField(widget=HiddenInput(), initial='oferta')
        context['kontrahent'] = get_object_or_404(Kontrahent, pk=self.kwargs.get('kontrahent', None))
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context


class OfertaDelete(LoginRequiredMixin, generic.DeleteView):
    model = Oferta
    success_message = 'Oferta została pomyślnie usunięta.'

    def get_success_url(self):
        return reverse_lazy('escrm:kontrahent-oferty', kwargs={'pk': self.object.kontrahent.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(OfertaDelete, self).delete(request, *args, **kwargs)


class OfertaUpdate(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Oferta
    form_class = OfertaEditForm
    template_name = 'escrm/oferta_update.html'
    success_message = 'Zmiany zostały zapisane.'

    def get_success_url(self):
        return reverse_lazy('escrm:kontrahent-oferty', kwargs={'pk': self.object.kontrahent.pk})


class OfertyDlaKontrahenta(LoginRequiredMixin, generic.ListView):
    model = Oferta
    template_name = 'escrm/oferta_list.html'
    # context_object_name = 'lista_ofert'

    def get_context_data(self, **kwargs):
        context = super(OfertyDlaKontrahenta, self).get_context_data(**kwargs)
        kontrahent = get_object_or_404(Kontrahent, pk=self.kwargs['pk'])
        context['kontrahent'] = kontrahent
        context['lista_ofert'] = Oferta.objects.filter(kontrahent=kontrahent)
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context


# Umowy


def umowa_valid(request, pk):
    agree_form = UmowaForm(request.GET)
    context = dict()
    kontrahent = get_object_or_404(Kontrahent, pk=pk)
    bounded_agreement_form = render_to_string('escrm/umowa/agreement.html', {'form_umowa': agree_form,
                                                                            'kontrahent': kontrahent}, request)
    if not agree_form.is_valid():
        context['is_valid'] = 'False'
    else:
        context['is_valid'] = 'True'
        payment_form = PlatnoscForm()
        payment_form_rendered = render_to_string('escrm/umowa/payment.html', {'form_platnosc': payment_form}, request)
        context['payment_form'] = payment_form_rendered
    context['agreement_form'] = bounded_agreement_form
    return JsonResponse(context)


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def add_months(sourcedate,months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)


class UmowaCreate(LoginRequiredMixin, generic.View):
    ctx = dict()
    template = 'escrm/umowa_form.html'

    def get(self, request, pk):
        kontrahent = get_object_or_404(Kontrahent, id_kontrahenta=pk)
        self.ctx['kontrahent'] = kontrahent
        self.ctx['form_umowa'] = UmowaForm(initial={'kontrahent': kontrahent})
        self.ctx['form_platnosc'] = PlatnoscForm()
        return render(request, self.template, self.ctx)

    def post(self, request, pk):
        agree_form = UmowaForm(request.POST)
        payment_form = PlatnoscForm(request.POST)
        if agree_form.is_valid():
            if payment_form.is_valid():
                agree_form.instance.opiekun = self.request.user.profil
                agreement = agree_form.save()
                if payment_form.cleaned_data.get('type') == 'jednorazowa':
                    once_date = payment_form.cleaned_data.get('once_date')
                    payment = Platnosc.objects.create(umowa=agreement,
                                                      kwota=agreement.wartosc,
                                                      termin=once_date,
                                                      kwota_zaksiegowana=0)
                    return render(request, 'escrm/umowa/agreement_success.html', {'payment_object': payment})
                elif payment_form.cleaned_data.get('type') == 'cykliczna':
                    end_date = payment_form.cleaned_data.get('cyclic_end_date')
                    datediff = diff_month(end_date, datetime.datetime.now())
                    monthly_payment = agreement.wartosc / datediff
                    payment_list = list()
                    for month in range(datediff):
                        date = add_months(datetime.datetime.now(), month+1)
                        if payment_form.cleaned_data.get('cyclic_type') == 'pierwszego':
                            date = date.replace(day=1)
                        elif payment_form.cleaned_data.get('cyclic_type') == 'okreslonego':
                            day = payment_form.cleaned_data.get('cyclic_day')
                            date = date.replace(day=day)
                        elif payment_form.cleaned_data.get('cyclic_type') == 'ostatniego':
                            last_day_of_month = calendar.monthrange(date.year, date.month)[1]
                            date = date.replace(day=last_day_of_month)
                        payment = Platnosc.objects.create(umowa=agreement,
                                                          kwota=ceil(monthly_payment * 100) / 100.0,
                                                          termin=date,
                                                          kwota_zaksiegowana=0)
                        payment_list.append(payment)
                    return render(request, 'escrm/umowa/agreement_success.html', {'payment_list': payment_list})
            self.ctx['kontrahent'] = agreement.kontrahent
            self.ctx['form_umowa'] = agree_form
            self.ctx['form_platnosc'] = payment_form
            return render(request, self.template, self.ctx)


class UmowaDetail(LoginRequiredMixin, generic.DetailView):
    model = Umowa
    form_dokument = DokumentForm()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_dokument'] = self.form_dokument
        context['form_dokument'].fields['nazwa_pliku'].required = False
        context['form_dokument'].fields['tytul_dokumentu'].required = False
        context['form_dokument'].fields['typ'] = CharField(widget=HiddenInput(), initial='umowa')
        context['kontrahent'] = get_object_or_404(Kontrahent, pk=self.kwargs.get('kontrahent', None))
        context['platnosc_set'] = self.object.platnosc_set.all()
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context


class UmowaDelete(LoginRequiredMixin, generic.DeleteView):
    model = Umowa
    success_message = 'Umowa została pomyślnie usunięta.'

    def get_success_url(self):
        return reverse_lazy('escrm:kontrahent-umowy', kwargs={'pk': self.object.kontrahent.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(UmowaDelete, self).delete(request, *args, **kwargs)


class UmowyDlaKontrahenta(LoginRequiredMixin, generic.ListView):
    model = Umowa
    template_name = 'escrm/umowa_list.html'

    def get_context_data(self, **kwargs):
        context = super(UmowyDlaKontrahenta, self).get_context_data(**kwargs)
        kontrahent = get_object_or_404(Kontrahent, pk=self.kwargs['pk'])
        context['kontrahent'] = kontrahent
        context['lista_umow'] = Umowa.objects.filter(kontrahent=kontrahent)
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context


class UmowaUpdate(LoginRequiredMixin, SuccessMessageMixin, generic.UpdateView):
    model = Umowa
    fields = ['temat', 'produkt', 'termin_waznosci', 'wartosc', 'status'
               ,'data_platnosci', 'waluta', 'termin_platnosci']
    template_name = 'escrm/umowa_update.html'
    success_message = 'Zmiany zostały zapisane.'

    def get_success_url(self, **kwargs):
        return reverse_lazy('escrm:kontrahent-umowy', kwargs={'pk': self.kwargs.get('pk'), })


class PlatnoscUpdate(LoginRequiredMixin, generic.UpdateView):
    model = Platnosc
    fields = ['termin', 'kwota', 'kwota_zaksiegowana']
    template_name = 'escrm/platnosc_update.html'
    success_message = 'Zapisano zmiany dotyczące płatności nr '

    def get_success_url(self):
        pk = self.umowa.pk
        kontrahent = self.umowa.kontrahent.pk
        return reverse_lazy('escrm:umowa-detail', kwargs={'pk': pk, 'kontrahent': kontrahent})

    def get_success_message(self):
        return self.success_message + self.pk


# ZDARZENIE


class ZdarzenieList(LoginRequiredMixin, generic.ListView):
    model = Zdarzenie

    def get_context_data(self, **kwargs):
        context = super(ZdarzenieList, self).get_context_data(**kwargs)
        if 'pk' in self.request.GET:
            kontrahent = get_object_or_404(Kontrahent, pk=self.kwargs['pk'])
            context['kontrahent'] = kontrahent
            context['lista_zdarzen'] = Zdarzenie.objects.filter(kontrahent=kontrahent).order_by('-id_zdarzenia')

        context['lista_zdarzen'] = Zdarzenie.objects.all().order_by('-id_zdarzenia')
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context


class ZdarzenieDetail(LoginRequiredMixin, generic.DetailView):
    model = Zdarzenie

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context


class ZdarzenieCreate(LoginRequiredMixin, generic.CreateView):
    model = Zdarzenie
    form_class = ZdarzenieForm

    def form_valid(self, form):
        form.instance.uzytkownik = self.request.user.profil
        return super(ZdarzenieCreate, self).form_valid(form)

    def get_initial(self):
        initial = super(ZdarzenieCreate, self).get_initial()
        self.kontrahent = get_object_or_404(Kontrahent, id_kontrahenta=self.kwargs.get('pk'))
        initial['kontrahent'] = self.kontrahent
        if 'id_typu' in self.request.GET:
            pk = self.request.GET.get('id_typu')
            initial['typ'] = TypZdarzenia.objects.get(pk=pk)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kontrahent'] = self.kontrahent
        context['next'] = self.request.META.get('HTTP_REFERER')
        context['breadcrumb_name'] = "Lista zdarzeń"
        return context

    def get_success_url(self):
        # success_url = self.request.META.get('HTTP_REFERER')
        return reverse_lazy('escrm:kontrahent-zdarzenia',  kwargs={'pk': self.kwargs.get('pk')})
        # return success_url


class ZdarzenieUpdate(LoginRequiredMixin, generic.UpdateView):
    model = Zdarzenie
    fields = ['data_zdarzenia', 'temat', 'typ', 'notatka']

    def get_success_url(self):
        return reverse_lazy('escrm:zdarzenie-list')

    def get_initial(self):
        initial = super(ZdarzenieUpdate, self).get_initial()
        if 'id_kontrahenta' in self.request.GET:
            pk = self.request.GET.get('id_kontrahenta')
            initial['kontrahent'] = Kontrahent.objects.get(pk=pk)
        if 'id_typu' in self.request.GET:
            pk = self.request.GET.get('id_typu')
            initial['typ'] = TypZdarzenia.objects.get(pk=pk)
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context


class ZdarzenieDelete(LoginRequiredMixin, generic.DeleteView):
    model = Zdarzenie
    success_message = 'Zdarzenie zostało pomyślnie usunięte.'
    success_url = '/escrm/zdarzenie/'

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super(ZdarzenieDelete, self).delete(request, *args, **kwargs)


class ZdarzeniaDlaKontrahenta(LoginRequiredMixin, generic.ListView):
    model = Zdarzenie
    template_name = 'escrm/zdarzenie_list.html'

    def get_context_data(self, **kwargs):
        context = super(ZdarzeniaDlaKontrahenta, self).get_context_data(**kwargs)
        kontrahent = get_object_or_404(Kontrahent, pk=self.kwargs['pk'])
        context['kontrahent'] = kontrahent
        context['next'] = self.request.META.get('HTTP_REFERER')
        context['lista_zdarzen'] = Zdarzenie.objects.filter(kontrahent=kontrahent.pk)
        return context


# WIDOKI DLA OPIEKUNA


class OpiekunKlienci(LoginRequiredMixin, generic.ListView):
    model = Kontrahent
    template_name = 'escrm/kontrahent_list.html'

    def get_context_data(self, **kwargs):
        context = super(OpiekunKlienci, self).get_context_data(**kwargs)
        context['lista_kontrahentow'] = Kontrahent.objects.filter(opiekun=self.request.user.profil)
        context['breadcrumb_name'] = 'Moi klienci'
        context['next'] = self.request.META.get('HTTP_REFERER')
        return context


class OpiekunUmowy(LoginRequiredMixin, generic.ListView):
    model = Umowa
    template_name = 'escrm/dashboard/moje_umowy.html'

    def get_context_data(self, **kwargs):
        context = super(OpiekunUmowy, self).get_context_data(**kwargs)
        context['lista_umow'] = Umowa.objects.filter(opiekun=self.request.user.profil)
        return context


class OpiekunOferty(LoginRequiredMixin, generic.ListView):
    model = Oferta
    template_name = 'escrm/dashboard/moje_oferty.html'

    def get_context_data(self, **kwargs):
        context = super(OpiekunOferty, self).get_context_data(**kwargs)
        context['lista_ofert'] = Oferta.objects.filter(opiekun=self.request.user.profil)
        return context


class OpiekunZdarzenia(LoginRequiredMixin, generic.ListView):
    model = Zdarzenie
    template_name = 'escrm/dashboard/moje_zdarzenia.html'

    def get_context_data(self, **kwargs):
        context = super(OpiekunZdarzenia, self).get_context_data(**kwargs)
        context['lista_zdarzen'] = Zdarzenie.objects.filter(uzytkownik=self.request.user.profil)
        context['breadcrumb_name'] = 'Moje zdarzenia'
        context[ 'next' ] = self.request.META.get('HTTP_REFERER')
        return context
