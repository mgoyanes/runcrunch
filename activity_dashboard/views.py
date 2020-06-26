from django.shortcuts import render, redirect
from plotly.offline import plot
from django_plotly_dash import DjangoDash
from django.contrib.auth.decorators import login_required
from . import forms

import os
import datetime
import asyncio
import psycopg2 as psy

from activity_dashboard.dash_apps.finished_apps import driver
from scripts import postgres as db
from scripts import helper

METRICS = {
        'dist': 'Distance',
        'time': 'Time',
        'elev': 'Elevation',
        'pace': 'Pace',
        'avg_hr': 'Heartrate',
        'intensity': 'Intensity',
        'schedule': 'Schedule View'
        }

@login_required(redirect_field_name='/login')
def activity_dashboard(request):
    try:
        s = datetime.datetime.strptime(request.POST.get('start'), '%m/%d/%y')
        f = datetime.datetime.strptime(request.POST.get('end'), '%m/%d/%y')
    except:
        f = helper.next_sunday(datetime.datetime.today()).date()
        s = f - datetime.timedelta(days = 20)

    USER = request.user
    athlete = driver.get_athlete(USER)

    try:
        date_picker = forms.DateForm(request.POST)
        quick_links = forms.QuickLinks(request.POST)
        context = {'date_picker': date_picker, 'quick_links': quick_links}

        if request.method == "POST":
            if 'custom_sub' in request.POST: # Date Picker
                if date_picker.is_valid():
                    s = min(date_picker.cleaned_data['date_start'],
                            date_picker.cleaned_data['date_end'])
                    f = max(date_picker.cleaned_data['date_start'],
                            date_picker.cleaned_data['date_end'])
                else:
                    date_picker = forms.DateForm()
            elif 'quick_links_sub' in request.POST: # Quick Links
                if quick_links.is_valid():
                    s, f = driver.quick_links(quick_links.cleaned_data)
                context['quick_links'] = forms.QuickLinks({'quick_items': 0, 'quick_links': quick_links.cleaned_data['quick_links']})
            context['date_picker'] = forms.DateForm({'date_start': s, 'date_end': f})
        else:
            context['date_picker'] = forms.DateForm({'date_start': s, 'date_end': f})

        # Plot graphs and add to context if valid
        *graphs_objs, info, last7, view_stats, month_stats, yr_stats = driver.activity_dashboard(athlete, s, f)

        for i in range(10):
            context[f'g{i}'] = graphs_objs[i]

        context.update({
                'info': info,
                'last7': last7,
                'view_stats': view_stats,
                'month_stats': month_stats,
                'year_stats': yr_stats,
                'athlete': athlete
                })

        return render(request, 'activity_dashboard/activity_dashboard.html', context)
    except:
        return redirect('/dashboard/error')

@login_required(redirect_field_name='/login')
def activity_detail(request, activity_id):
    user = request.user

    try:
        athlete = driver.get_athlete(user, activity_id)
    except LookupError:
        return redirect('/')

    shareable_key = ''
    if request.method == 'POST':
        import string
        import random

        shareable_key = ''.join(random.choices(string.ascii_letters + string.digits, k = 25))
        db.UPDATE('activities', where=f'activity_id = {activity_id}', numCols=1,
                  cols='shareable_key', vals=f"'{shareable_key}'")

    if athlete['unit'] == 'imperial':
        units = {'dist': 'mi', 'elev': 'ft'}
    else:
        units = {'dist': 'km', 'elev': 'ft'}

    context = {'athlete': athlete, 'units': units, 'shareable_key': shareable_key,
               'activity_id': activity_id}

    run_info, weather, streams, streams_laps, map_stream = driver.activity_details(athlete, activity_id)

    graph_dict = dict.fromkeys([f'g{i}' for i in range(9)], '')

    try:
        graphs, tables = asyncio.run(driver.graphs(athlete, run_info, streams, streams_laps, map_stream))
        for k, v in graph_dict.items():
            if k in graphs:
                graph_dict[k] = graphs[k]
    except:
        tables = ['','']

    context.update(graph_dict)
    context.update({
            'auto_table': tables[0],
            'device_table': tables[1],
            'run_info': run_info,
            'weather': weather,
            'id': activity_id
            })

    return render(request, 'activity_dashboard/activity_detail.html', context)

@login_required(redirect_field_name='/login')
def heatmap(request):
    user = request.user
    try:
        athlete = driver.get_athlete(user)
        context = {'athlete': athlete}

        heatmap = driver.heatmap(athlete)

        context['heatmap'] = plot(heatmap, output_type='div',
               include_plotlyjs='cdn', config=dict(displayModeBar=False))

        return render(request, 'activity_dashboard/heatmap.html', context)
    except:
        return redirect('/dashboard/error')

@login_required(redirect_field_name='/login')
def trends(request):
    user = request.user

    try:
        metric_picker = forms.MetricPicker(request.POST)
        athlete = driver.get_athlete(user)

        context = {'metric_picker': metric_picker, 'athlete': athlete}

        if request.method == "POST":
            if metric_picker.is_valid():
                selected_metric = metric_picker.cleaned_data['metric']
            context['selected_metric'] = forms.MetricPicker({'metric': selected_metric})
        else:
            selected_metric = 'dist'

        *graphs, tb1, tb2 = driver.trends(athlete, selected_metric)
        graph_objs = tuple(zip(graphs, ['monthly', 'weekly', 'mega_hist', 'mega_box']))

        for g, name in graph_objs:
            if g != None:
                context[name] = plot(g, output_type='div',
                       include_plotlyjs='cdn', include_mathjax='cdn',
                       config=dict(displayModeBar=False))
            else:
                context[name] = ''

        context.update({
                'monthly_table': tb1,
                'weekly_table': tb2,
                'metric_picker': metric_picker,
                'metric': METRICS[selected_metric]
                })

        return render(request, 'activity_dashboard/trends.html', context)
    except:
        return redirect('/dashboard/error')

def error(request):
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    athlete = driver.get_athlete(request.user)
    pr_form = forms.PersonalRecord(request.POST)

    if pr_form.is_valid():
        pr_info = pr_form.cleaned_data
        time = (int(pr_info['h'])*3600)+(int(pr_info['m'])*60)+int(pr_info['s'])
        if pr_info['unit'] == 'mi':
            dist = int(pr_info['distance']*1609.34 + 0.5)
        elif pr_info['unit'] == 'km':
            dist = int(pr_info['distance']*1000 + 0.5)
        else:
            dist = pr_info['distance']

        db.UPDATE('athletes', where=f"username = '{request.user}'", numCols=2, cols='pr_time, pr_distance', vals=f"{time}, {dist}")
        conn.close()
        return redirect('/dashboard/error')
    else:
        pr_form = forms.PersonalRecord()

    conn.close()
    return render(request, 'activity_dashboard/error.html', {'pr_form': pr_form, 'athlete': athlete})

@login_required(redirect_field_name='/login')
def privacy(request):
    athlete = driver.get_athlete(request.user)

    return render(request, 'activity_dashboard/privacy.html', {'athlete': athlete})

def shareable(request, activity_id, key):

    activity = db.SELECT('activities', where=f"activity_id = {activity_id} AND shareable_key = '{key}'")
    if not activity:
        return redirect('/')

    athlete = db.SELECT('athletes', where=f"a_id = {activity['a_id']}")
    athlete = driver.get_athlete(athlete['username'])
    athlete['profile_pic'] = None

    if athlete['unit'] == 'imperial':
        units = {'dist': 'mi', 'elev': 'ft'}
    else:
        units = {'dist': 'km', 'elev': 'ft'}

    context = {'athlete': athlete, 'units': units, 'shareable_key': 'PUBLIC'}

    run_info, weather, streams, streams_laps, map_stream = driver.activity_details(athlete, activity_id)

    graph_dict = dict.fromkeys([f'g{i}' for i in range(9)], '')

    try:
        graphs, tables = asyncio.run(driver.graphs(athlete, run_info, streams, streams_laps, map_stream))
        for k, v in graph_dict.items():
            if k in graphs:
                graph_dict[k] = graphs[k]
    except:
        tables = ['','']

    context.update(graph_dict)
    context.update({
            'auto_table': tables[0],
            'device_table': tables[1],
            'run_info': run_info,
            'weather': weather,
            'id': activity_id
            })

    return render(request, 'activity_dashboard/activity_detail.html', context)

    return render(request)

@login_required(redirect_field_name='/login')
def edit(request, activity_id):
    athlete = driver.get_athlete(request.user)
    manual_edit = forms.ManualEdit(request.POST)
    context = {'athlete': athlete, 'manual': manual_edit}

    if request.method == "POST" and 'manual' in request.POST:
        if manual_edit.is_valid():
            data = manual_edit.cleaned_data
            #driver.upload(data)
        else:
            manual_edit = forms.ManualActivity()

    return render(request, 'activity_dashboard/new.html', context)