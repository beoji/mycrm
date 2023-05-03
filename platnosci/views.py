import datetime
from calendar import *
from datetime import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import generic

from escrm.models import Platnosc
from .forms import PlatnoscForm


class CalendarView(LoginRequiredMixin, generic.View):
    template = 'platnosci/kalendarz.html'
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        year = request.GET.get('y')
        month = request.GET.get('m')
        day = request.GET.get('d')
        context = dict()
        context['year'] = year
        context['month'] = month
        context['day'] = day
        # Metoda pobiera dane z GET-a i dolacza
        context['info'] = self.get_event_list(context)
        # do nich liste zadan w tym dniu
        context['pay_queryset'] = Platnosc.objects.filter(termin__year=year).filter(termin__month=month)
        # Metoda zwracająca `queryseta` z płatnościami
        # danego miesiąca
        calendar = Calendar(firstweekday=0)
        # Konstruktor kalendarza i metoda zwracajaca miesiac w postaci tableli
        month_object = calendar.monthdays2calendar(int(year), int(month))
        context['month_object'] = month_object
        return render(request, self.template, context)

    def get_event_list(self, context):
        day = int(context['day'])
        month = int(context['month'])
        year = int(context['year'])
        events_today = Platnosc.objects.filter(
            termin=datetime.date(year, month, day)
        )
        print(events_today)
        return events_today


class PaymentListView(LoginRequiredMixin, generic.View):
    template = 'platnosci/lista.html'
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    def get(self, request):
        context = dict()
        payments = Platnosc.objects.all()
        query_months = Platnosc.objects.dates('termin', 'month').distinct()
        p = dict()
        for month in query_months:
            p[month] = list()
            for pay in payments:
                if pay.termin.month == month.month:
                    p[month].append(pay)
        context['list'] = p
        return render(request, self.template, context)


def get_payment_data(request, pk):
    context = dict()
    obj = Platnosc.objects.get(pk=pk)
    print(obj)
    context['form'] = PlatnoscForm(instance=obj)
    template_name = 'platnosci/snippets/modal_payment.html'
    rendered_form = render_to_string(template_name, context, request)
    data = dict()
    data['modal'] = rendered_form
    return JsonResponse(data)


def save_payment_data(request, pk):
    context = dict()
    data = dict()
    obj = Platnosc.objects.get(pk=pk)
    payment_form = PlatnoscForm(request.POST, instance=obj)
    if payment_form.is_valid():
        payment_form.save()
        data['result'] = 'success'
    else:
        template_name = 'platnosci/snippets/modal_payment.html'
        context['form'] = payment_form
        rendered_form = render_to_string(template_name, context, request)
        data['modal'] = rendered_form
        data['result'] = 'failed'
    return JsonResponse(data)
