from django.shortcuts import render, redirect
from django.views.generic.base import View
from .forms import RegistrationForm
from .services import create_new_user, create_new_player, new_user_auto_loging


class RegistrationView(View):

    def get(self, request):
        registration_form = RegistrationForm()
        context = {'registration_form': registration_form}
        return render(request, 'registration/registration_form.html', context)

    def post(self, request):
        reg_form = RegistrationForm(request.POST)
        if request.method == 'POST' and reg_form.is_valid():
            user = create_new_user(reg_form)
            player = create_new_player(user, request, reg_form)
            new_user_auto_loging(reg_form, request)
            return redirect('index')
        else:
            context = {'registration_form':reg_form, 'method': request.method, 'valid_form': reg_form.is_valid()}
            return render(request, 'registration/bad_request.html', context)


