from django.shortcuts import render
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

import psycopg2 as psy
import os
import time as tm
import pandas as pd

from activity_dashboard.dash_apps.finished_apps import driver
from scripts import helper
from scripts import postgres as db
from .scripts import scripts
from .scripts import importer

def register(request):

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username=form.cleaned_data['username']
            new_user = authenticate(username=username,
                                    password=form.cleaned_data['password1'])
            login(request, new_user)
            return redirect('/account')
    else:
        form = UserCreationForm()

    return render(request, 'register/register.html', {'form': form})

@login_required(redirect_field_name='/login')
def connect_to_strava(request):
    body = dict(request.GET.items())
    if 'activity:read' not in body['scope']:
        return redirect(f"https://www.strava.com/oauth/authorize?client_id={os.environ['STRAVA_CLIENT_ID']}&redirect_uri=https%3A%2F%2Fwww.run-crunch.com%2Fconnect-to-strava&approval_prompt=auto&response_type=code&scope=activity%3Aread%2Cactivity%3Aread_all")

    print(dict(request.GET.items()))
    print('code:', request.GET.get('code', ''))
    print('user:', request.user)

    code = request.GET.get('code', '')

    try:
        success = driver.add_new_athlete(request.user, code)
    except:
        success = False

    if success:
        return redirect('/account')
    else:
        return render(request, 'home/connect_to_strava.html', {'success': success})

def login_user(request):
    response = redirect('/dashboard')
    return response

def home(request):
    return render(request, 'home/home.html', {})

def delete(request):
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    try:
        db.DELETE('auth_user', where=f"username = '{request.user}'")
    except: # All Auth user
        cur = conn.cursor()
        cur.execute(f"SELECT id FROM auth_user WHERE username = '{request.user}'")
        user_id = cur.fetchone()[0]
        cur.close()
        db.DELETE('socialaccount_socialaccount', where=f"user_id = {user_id}")
        db.DELETE('auth_user', where=f"username = '{request.user}'")
    conn.close()
    return redirect('/')

@login_required(redirect_field_name='/login')
def account(request):
    from . import forms

    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    context = {'strava_client_id': os.environ['STRAVA_CLIENT_ID']}

    try:
        # Load athlete info
        athlete = db.SELECT('athletes', where=f"username = '{request.user}'", conn=conn)
        unit = athlete['unit']

        # Best Effort
        be_time = tm.strftime('%H:%M:%S', tm.gmtime(athlete['pr_time']))
        be_dist = '{:,}'.format(athlete['pr_dist'])
        be_km = round(athlete['pr_dist']/1000, 2)
        be_mi = round(athlete['pr_dist']*0.000621371, 2)

        # Get all runs
        all_runs = db.SELECT('activities', where=f"a_id = {athlete['a_id']}", conn=conn)
        if type(all_runs) is not list:
            all_runs = [all_runs]
        all_runs = pd.DataFrame(all_runs)
        try:
            totals = scripts.account_totals(all_runs, athlete, unit)
            print('TOTALS:\n', totals)

            for k, v in totals.items():
                context[k] = v
        except:
            totals = None
    except:
        athlete = ''
        be_time = '06:30'
        be_dist = 1609
        be_km = 1.609
        be_mi = 1
        return render(request, 'home/connect_to_strava.html', {})

    # PR form
    pr_form = forms.PersonalRecord(request.POST)
    unit_preference = forms.UnitPreference(request.POST)
    import_form = forms.ImportRuns(request.POST)
    email_form = forms.EmailForm(request.POST)

    if request.method == 'POST':
        if 'pr_sub' in request.POST:
            if pr_form.is_valid():
                pr_info = pr_form.cleaned_data
                time = (int(pr_info['h'])*3600)+(int(pr_info['m'])*60)+int(pr_info['s'])
                if pr_info['unit'] == 'mi':
                    dist = int(pr_info['distance']*1609.34 + 0.5)
                elif pr_info['unit'] == 'km':
                    dist = int(pr_info['distance']*1000 + 0.5)
                else:
                    dist = pr_info['distance']

                db.UPDATE('athletes', where=f"username = '{request.user}'", numCols=2,
                          cols='pr_time, pr_distance', vals=f"{time}, {dist}", conn=conn)
                conn.close()
                return redirect('/account')
            else:
                pr_form = forms.PersonalRecord()
        elif 'unit_sub' in request.POST:
            if unit_preference.is_valid():
                unit_pref = unit_preference.cleaned_data['metric']

                db.UPDATE('athletes', where=f"username = '{request.user}'", numCols=1,
                          cols='unit', vals=f"'{unit_pref}'", conn=conn)
                conn.close()
                return redirect('/account')
            else:
                unit_preference = forms.UnitPreference()
        elif 'import_runs' in request.POST:
           #try:
           importer.import_runs(athlete)
           db.UPDATE('athletes', where=f"username = '{request.user}'",
                     numCols=1, cols='imported', vals="'Y'", conn=conn)
           return redirect('/dashboard')
           #except:
           #    context.update({'error': True})
        elif 'email_sub' in request.POST:
            if email_form.is_valid():
                email = email_form.cleaned_data['email']
                db.UPDATE('auth_user', where=f"username = '{request.user}'",
                      numCols=1, cols='email', vals=f"'{email}'", conn=conn)
            else:
                email_form = forms.EmailForm()

    context.update({
        'pr_form': pr_form,
        'unit_preference': unit_preference,
        'import_form': import_form,
        'email_form': email_form,
        'athlete': athlete,
        'be_time': be_time,
        'be_dist': be_dist,
        'be_km': be_km,
        'be_mi': be_mi,
        })

    try:
        conn.close()
    except:
        pass

    return render(request, 'home/account.html', context)

def privacy(request):
    return render(request, 'home/privacy_policy.html', {})