from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import Http404
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from escrm.models import Profil
from esdjango.forms import UserForm
from esdjango.forms import ProfilForm


def cust_login(request):
    if request.user.is_staff:
        return redirect('/admin/')
    elif request.user.groups.filter(name="ksiegowy").exists():
        return redirect('/platnosci/')
    elif request.user.groups.filter(name="recepcja").exists():
        return redirect('/korespondencja/')
    else:
        return redirect('/escrm/')


@login_required
def reset_denied(request):
    return render(request, 'common/reset_denied.html')


@login_required
def profil(request):
    try:
        p = Profil.objects.get(user=request.user)
    except Profil.DoesNotExist:
        raise Http404("Nie ma profilu")
    return render(request, 'common/profil.html', {'profil': p})


@login_required
@transaction.atomic
def update_profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfilForm(request.POST, instance=request.user.profil)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Twój profil został zaktualizowany')
            return redirect('profil')
        else:
            messages.error(request, 'Formularz zawiera błędy.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfilForm(instance=request.user.profil)
    return render(request, 'common/profil_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required()
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Twoje hasło zostało pomyślnie zmienione')
            return redirect('change_password')
        else:
            messages.error(request, 'Formularz zawiera błędy')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'registration/password_change_form.html', {
        'form': form
    })
