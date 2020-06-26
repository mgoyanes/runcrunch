# -*- coding: utf-8 -*-
"""
Created on Thu May 28 23:13:52 2020

@author: sferg
"""
import plotly.graph_objects as go
import datetime as dt
import numpy as np
import math

from scripts import helper
from scripts import constants

COLORS = constants.COLORS
INTENSITYSCALE = constants.INTENSITYSCALE
INTENSITY_SCALE_LINE = constants.INTENSITYSCALE_LINE

def hoverInfo(run, unit):
    if unit == 'imperial':
        c = ('mi', 'ft', '/mi')
    else:
        c = ('km', 'm', '/km')
    try:
        name = run['name'] + '<br>'
    except:
        name = ''
    try:
        date = run['date'].strftime('%a, %m/%d/%y')  + '<br>'
    except:
        date = ''
    try:
        dist = 'Dist: ' + str(convert(run['dist'], 'dist', unit, error=True)) + f' {c[0]}<br>'
    except:
        dist = ''
    try:
        time = 'Time: ' + convert(run['time'], 'time', unit, error=True) + '<br>'
    except:
        time = ''
    try:
        pace = 'Pace: ' + convert(run['velocity'], 'velocity', unit, error=True) + f' {c[2]}<br>'
    except:
        pace = ''
    try:
        elev = 'Elev: ' + str(convert(run['elev'], 'elev', unit, error=True)) + f' {c[1]}<br>'
    except:
        elev = ''
    try:
        hr = 'HR: ' + str(convert(run['avg_hr'], 'avg_hr', unit, error=True)) + ' bpm<br>'
    except:
        hr = ''
    try:
        intensity = 'Intensity: ' +  str(convert(run['intensity'], 'intensity', unit, error=True)) + '%<br>'
    except:
        intensity = ''

    res = f"<b>{name}{date}{dist}{time}{pace}{elev}{hr}{intensity}</b>"

    return res

def tickLabels(bars, metric, unit):
    y_vals = [b['y'] for b in bars] # 2D array of y values

    if metric == 'intensity':
        maxes = list(np.max(np.array(y_vals), axis=0)) # just get max values
        labs = [f"<b>{h}</b>" if str(h) != '0' else '' for h in maxes]
    elif metric == 'velocity' or metric == 'avg_hr':
        arr = np.array(y_vals)
        arr = arr.astype('float')
        arr[arr == 0] = np.nan
        avgs = list(np.nanmean(arr, axis=0)) # avg for each day in range
        labs = ['' if math.isnan(h) else f"<b>{convert(h, metric, unit)}</b>" for h in avgs]
    else:
        totals = list(np.sum(np.array(y_vals), axis=0)) # Sum cols
        labs = ['<b>'+str(convert(float(h), metric, unit))+'</b>' if str(h) != '0' else '' for h in totals]

    return labs

def weekly_spans(bars, start, end, index, metric, unit):
    vals = np.array([b['y'] for b in bars])
    line_points = [-.5]
    tick_points = []
    tick_text = []

    # If just one week, return a mini-span
    if (end-start).days < 7:
        tick_points = [index[-1]/2]
        tick_text = [weekly_totals(vals, start, end, metric, unit)]
        line_points += [index[-1] + 0.5]
        return line_points, tick_points, tick_text

    # First mini-span
    mon_index = 0
    mon = start
    if start.weekday() != 0:
        while mon.weekday() != 0:
            mon = mon + dt.timedelta(days=1)
            mon_index += 1

        # create first span
        tick_points.append((mon_index-1)/2)
        tick_text.append(weekly_totals(vals[:, 0:mon_index], start,
                                       mon-dt.timedelta(days=1), metric, unit))
        start = mon # align start to first monday

    # Last span
    if end.weekday() != 6:
        last_sun_index = 0
        last_sun = end
        while last_sun.weekday() != 6:
            last_sun = last_sun - dt.timedelta(days=1)
            last_sun_index += 1

        # create last span
        tick_points.append(len(index) - (last_sun_index/2) - 0.5)
        tick_text.append(weekly_totals(vals[:, -(last_sun_index):],
                                       last_sun + dt.timedelta(days=1), end,
                                       metric, unit))
        end = last_sun # align end to last sunday
        line_points += [index[-1] - last_sun_index+.5]

    # Bulk of spans
    if start < end:
        # create spans until last sunday
        num_weeks = int(((end-start).days+1)/7)
        s = mon_index

        for w in range(num_weeks):
            # append divider
            line_points.append(s + w*7 -.5)
            # append tick point
            tick_points.append(s + w*7 + 3)
            # append tick text
            tick_text.append(weekly_totals(vals[:, s + w*7:s + w*7 + 7],
                                           mon + dt.timedelta(days=w*7),
                                           mon + dt.timedelta(days=w*7 + 6),
                                           metric, unit))

    line_points += [index[-1]+.5] # last divider

    return line_points, tick_points, tick_text

def weekly_totals(vals, start, end, metric, unit):
    # only display range if > one day
    if start == end:
        week_range = start.strftime('%m/%d/%y')
    else:
        week_range = f"{start.strftime('%m/%d/%y')} - {end.strftime('%m/%d/%y')}"

    if metric == 'intensity':
        try:
            avg = int(sum(list(np.max(vals, axis=0)))/(end-start).days + 0.5)
        except: # only one day chosen
            try:
                avg = int(sum(list(np.sum(vals, axis=0))))
            except:
                avg = ''
        return f'{week_range}<br><b>{avg}%</b>'
    elif metric == 'velocity' or metric == 'avg_hr':
        sums = list(np.sum(vals, axis=0))
        num_runs = list(np.count_nonzero(vals, axis=0))
        try:
            avg = convert(float(sum(sums)/sum(num_runs)), metric, unit)
        except:
            avg = ''
        return f'{week_range}<br><b>{avg}</b>'
    else:
        sums = list(np.sum(vals, axis=0))
        try:
            total = convert(int(sum(sums)), metric, unit)
        except:
            total = ''
        return f'{week_range}<br><b>{total}</b>'

def convert(h, metric, unit, error=False):
    if h == 0:
        if error:
            raise AttributeError
        else:
            return ''

    if unit == 'imperial':
        c = (1609.34, 3.28084, 'mins/mile')
    else:
        c = (1000, 1, 'mins/km')

    convert = {
            'dist': round(h*(1/c[0]), 2),
            'elev': int(h*c[1]),
            'time': str(dt.timedelta(seconds=h)),
            'intensity': h,
            'velocity': helper.velocity_to_pace(h, _to=c[2]),
            'avg_hr': int(h+0.5),
            'kudos_count': int(h),
            'achievement_count': int(h)
            }

    # Omit first '0:' if less than an hour
    if metric == 'time':
        if convert['time'][0] == '0':
            convert['time'] = convert['time'][2:]

    return convert[metric]

async def unpack_runs(runs, stacks, index, metric, unit):
    '''
    Returns a list of lists
    The outer list corresponds to each layer in the stack
    the inner list contains a height for each day in the index
    '''
    hovertext = []
    heights = []
    links = []
    for i in range(stacks):
        h = []
        h_text = []
        l = []
        for date in index:
            try:
                h.append(runs[date][i][metric])
                h_text.append(hoverInfo(runs[date][i], unit))
                l.append(f'<a href="{runs[date][i]["activity_id"]}"><b>View Run</b></a>')
            except:
                h.append(0)
                h_text.append('')
                l.append('')
        heights.append(h)
        hovertext.append(h_text)
        links.append(l)

    return (heights, hovertext, links, metric)

def intensity_color(pct):
    '''
    returns a text representation of the intensity pct
    '''
    pct *= 2
    if pct > 190:
        color, text = ('#fc0dec', 'Race')
    elif pct > 180:
        color, text = ("#fa0c0c", 'VO2 Max')
    elif pct > 160:
        color, text = ("#f29624", 'Tempo')
    elif pct > 140:
        color, text = ("#f5e616", 'Threshold')
    elif pct > 115:
        color, text = ("#3dd44c", 'Endurance - Hard')
    elif pct > 85:
        color, text = ("#6de3db", 'Endurance - Moderate')
    elif pct > 60:
        color, text = ("#75acff", 'Endurance - Easy')
    else:
        color, text = ('#5c5c5c', 'Recovery')

    return text

async def activities_chart(stacks, stack_vals, hovertext, links, index, end_date, delta, metric, unit):
    '''
    Set X axis values
    '''
    #base = end_date
    begin = end_date-dt.timedelta(days=delta)

    index_linear = list(range(0, len(index)))

    '''
    Create Figure Objects
    '''
    fig = go.Figure()
    bars = {} # dict of bars, keys = metric, values = list of bars (stacks)

    tmp= []

    for i in range(len(stack_vals)):

        colors = list(map(lambda v, c, i : c.format('1') if v > 0 else 'rgba(0,0,0,0)', stack_vals[i], [COLORS[f'run{i%4}']]*len(index_linear), [i]*len(index_linear)))

        bar = go.Bar(
                name=f"Run {i+1}",
                x=index_linear,
                y=stack_vals[i],
                xaxis='x2',
                yaxis='y2',
                width=1,
                marker=dict(
                        line=dict(
                                width=2,
                                color=colors,
                                ),
                        color=COLORS[f'run{i%4}'].format('.3')
                ),
                visible=True,
                hovertext=hovertext[i],
                hoverinfo='text'
            )

        tmp.append(bar)

    bars[metric] = tmp

    '''
    Create Weekly Span Lines
    '''
    line_points, tick_points, tick_text = weekly_spans(bars[metric], begin, end_date, index_linear, metric, unit)

    weekly_span_lines = go.Scatter(
        x=line_points,
        y=[0]*len(line_points),
        xaxis='x',
        yaxis='y',
        mode='lines+markers',
        hoverinfo='skip',
        marker=dict(
                symbol='line-ns',
                opacity=.25,
                color=COLORS['blueT'].format('.2'),
                size=1000,
                line=dict(
                        width=1.5,
                        color=COLORS['default']
                        )
                ),
        line=dict(
                color=COLORS['default'],
                width=2
                ),
        visible=True
        )

    '''
    Add Traces
    '''
    # Add weekly lines
    fig.add_trace(weekly_span_lines)

    for m in bars:
        for b in bars[m]:
            fig.add_trace(b)

    '''
    Layout
    '''
    if metric == 'velocity' or metric == 'avg_hr':
        vals = np.array([b['y'] for b in bars[metric]])
        sums = np.sum(vals, axis=0)
        miny = np.min(sums[np.nonzero(sums)])
        maxy = np.max(sums[np.nonzero(sums)])
        yaxis2 = dict(
                fixedrange=True,
                autorange=False,
                range=[.9*miny, 1.05*maxy],
                visible=False,
                overlaying='y',
                showgrid=False,
                domain=[0,1],
                )
    else:
        yaxis2 = dict(
                fixedrange=True,
                visible=False,
                overlaying='y',
                showgrid=False,
                domain=[0,1],
                )

    fig.update_layout(
            autosize=False,
            width=1150,
            height=400,
            paper_bgcolor=COLORS['transparent'],
            plot_bgcolor=COLORS['transparent'],
            margin=dict(
                    l=0,r=0,t=0,b=0,
                    autoexpand=True
                    ),
            uniformtext=dict(
                  minsize=1,
                  mode="show"
                  ),
            barmode='stack',
            hovermode='closest',
            showlegend=False,
            yaxis2=yaxis2,
            xaxis2=dict(
                    type='linear',
                    range=[-.6, len(index)-.4],
                    overlaying='x',
                    tickvals=index_linear,
                    ticktext=tickLabels(bars[metric], metric, unit),
                    automargin=True,
                    fixedrange=False,
                    zeroline=False,
                    ),
            yaxis=dict(
                    type='linear',
                    range=[0,1],
                    fixedrange=True,
                    visible=False,
                    showgrid=False,
                    ),
            xaxis=dict(
                    fixedrange=False,
                    range=[-.6,len(index)-.5],
                    matches='x2',
                    side='top',
                    showgrid=False,
                    zeroline=False,
                    # position text at midpoint of each week
                    tickvals=tick_points,
                    ticktext=tick_text
                    ),
            )
    '''
    Link Annotations
    '''
    #if len(index_linear) < 90: # huge performace hit
    link_text = []
    for s in range(stacks):
        for b in range(len(index_linear)):
            if bars[metric][s]['y'][b]:
                y = sum([bars[metric][i]['y'][b] for i in range(s+1)]) + 10
                link_text.append(
                        dict(
                                text=links[s][b],
                                bgcolor='rgba(255,255,255,.75)',
                                bordercolor=bars[metric][s]['marker']['line']['color'][b],
                                borderwidth=2,
                                borderpad=3,
                                height=10,
                                opacity=int(links[s][b] != ''),
                                showarrow=False,
                                visible=False,
                                xref='x2',
                                yref='y2',
                                yanchor='top',
                                x=index_linear[b],
                                y=y,
                                clicktoshow='onout',
                                xclick=index_linear[b],
                                yclick=bars[metric][s]['y'][b]
                        ))
    fig.update_layout(
            annotations=link_text
            )


    fig = fig.to_html(config={'displayModeBar': False}, include_plotlyjs='cdn',
                      full_html=False)

    return fig, metric

async def tod_chart(runs, end_date, delta):
    import plotly.figure_factory as ff

    '''
    Get range of dates and list of dates without any runs
    '''
    index = [(end_date - dt.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(delta+1)]
    no_runs = list(set(index) - {r['date'].strftime('%Y-%m-%d') for r in runs})

    '''
    Create bars for each day
    '''
    df = []
    for r in runs: # Add days w/ runs
        df.append(dict(
            Task=r['date'].strftime('%Y-%m-%d'),
            Start='2000-01-01 ' + dt.datetime.strftime(r['datetime'], '%H:%M'),
            Finish='2000-01-01 ' + dt.datetime.strftime(r['datetime'] + dt.timedelta(seconds=r['time']), '%H:%M'),
            Resource=intensity_color(r['intensity'])))

    for d in no_runs: # add placeholders for days w/o runs
        df.append(dict(
            Task=d,
            Start='2000-01-01 13:00',
            Finish='2000-01-01 13:00',
            Resource=''
            ))

    df = sorted(df, key=lambda x : x['Task'], reverse=True)

    '''
    Set colors based on intensity
    '''
    colors = dict(filter(lambda k : k[0] in ['Recovery',
                         'Endurance - Easy',
                         'Endurance - Moderate',
                         'Endurance - Hard',
                         'Threshold',
                         'Tempo',
                         'VO2 Max',
                         'Race', ''], COLORS.items()))
    '''
    Init figure
    '''
    fig = ff.create_gantt(df,
                          width=1150,
                          height=500,
                          colors=colors,
                          showgrid_x=True,
                          showgrid_y=True,
                          show_hover_fill=False,
                          bar_width=.5,
                          index_col='Resource',
                          show_colorbar=True,
                          group_tasks=True)

    '''
    Figure layout
    '''
    if delta > 21:
        y_min = delta - 21.5
    else:
        y_min = -0.5
    y_tickvals = [i for i in range(delta, -1,-1*((delta//22) + 1))]
    y_ticktext = [dt.datetime.strftime(end_date-dt.timedelta(days=i), '%a, %m/%d/%y') for i in y_tickvals][::-1]

    fig.update_layout(
            autosize=True,
            paper_bgcolor=COLORS['transparent'],
            plot_bgcolor=COLORS['transparent'],
            margin=dict(
                    l=0,r=0,t=0,b=0,
                    autoexpand=True
                    ),
            xaxis=dict(
                    rangeselector=None,
                    showspikes=True,
                    spikemode='across',
                    spikesnap='cursor',
                    showgrid=True,
                    gridcolor=COLORS['gray'],
                    tickformat='%I %p',
                    showticksuffix=None,
                    hoverformat='%I:%M %p'
                    ),
            yaxis=dict(
                    type='linear',
                    autorange=True,
                    spikemode='across',
                    spikesnap='data',
                    hoverformat='%a %m/%d/%Y',
                    tickmode='array',
                    tickvals=y_tickvals,
                    ticktext=y_ticktext,
                    tickformat='%a %m/%d/%Y',
                    ticks='outside',
                    tickson='boundaries',
                    showgrid=True,
                    gridcolor=COLORS['transparentGray']
                    ),
            hovermode='closest'
            )

    # set hover info
    for i in fig['data']:
        i['hoverinfo'] = 'x+name'

    return fig.to_html(include_plotlyjs='cdn', full_html=False,
                       config=dict(displayModeBar=False)), 'tod'

async def activities_table(runs, unit):
    import pandas as pd

    if type(runs) is not list:
        runs = [runs]

    df = pd.DataFrame(runs)
    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by='date',inplace=True, ascending=False)
    pace = [d['dist']/d['time'] if d['dist'] > 0 and d['time'] > 0 else None for i, d in df.iterrows()]
    df['pace'] = pace

    df = helper.format_dataframe(df, unit)

    df_html = df.to_html(index=False, escape=False) # replace <th> flags

    df_html = df_html[df_html.find('<tbody>'):df_html.find('</tbody>')] + '</tbody>'

    df_html = df_html.replace('<tr>0</tr>', '<tr></tr>').replace('NaN', '')

    return df_html, 'table'
