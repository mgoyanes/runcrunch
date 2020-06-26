from django.shortcuts import render
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def register(request):

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username=form.cleaned_data['username']
            new_user = authenticate(username=username,
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect(f"/account")
    else:
        form = UserCreationForm()

    return render(request, 'register/register.html', {'form': form})

def login_user(request):
    response = redirect('/dashboard')
    return response