# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 18:27:07 2020

@author: sferg
"""
import pandas as pd
import numpy as np
import datetime as dt
import plotly.graph_objects as go
import plotly.figure_factory as ff

from scripts import constants
from scripts import helper

COLORS = constants.COLORS
INTENSITYSCALE = constants.INTENSITYSCALE

def convert_frame(frame, metric, unit):
    if unit == 'imperial':
        c = (0.000621371, 3.28084, 'mins/mile')
    else:
        c = (.001, 1, 'mins/km')

    if metric == 'dist':
        return list(map(lambda x : x*c[0], frame))
    if metric == 'elev':
        return list(map(lambda x : x*c[1], frame))
    if metric == 'pace':
        res = []
        for x in frame:
            if x > 2:
                p = 1/(x * c[0])
                m = (p%3600)//60
                s = p%60
                if m == 0:
                    res.append(dt.datetime(year=2000, month=1, day=1, hour=0,
                                           minute=0, second=int(round(s))))
                elif s == 0:
                    res.append(dt.datetime(year=2000, month=1, day=1, hour=0,
                                           minute=int(round(m)), second=0))
                else:
                    res.append(dt.datetime(year=2000, month=1, day=1, hour=0,
                                           minute=int(round(m)),
                                           second=int(round(m))))
        return res
    if metric == 'time':
        res = []
        for x in frame:
            if x > 0:
                res.append(dt.datetime(year=2000, month=1, day=1,
                                       hour=x//3600, minute=(x%3600)//60,
                                       second=x%60))
        return res

def convert(v, metric, unit):
    try:
        index = {
                'imperial': {
                        'dist': f"{'{:,}'.format(int(round(v*0.000621371, 2) + 0.5))} mi",
                        'time': helper.format_time(v),
                        'elev': f"{'{:,}'.format(int(v*3.28084+0.5))} ft",
                        'avg_hr': f"{int(v+0.5)}bpm",
                        'intensity': f'{int(v+0.5)}%',
                        'pace': f'{helper.velocity_to_pace(v)} /mi'
                        },
                'metric': {
                        'dist': f"{'{:,}'.format(int(round(v/1000, 0) + 0.5))} km",
                        'time': helper.format_time(v),
                        'elev': f"{'{:,}'.format(int(v+0.5))} m",
                        'avg_hr': f'{int(v+0.5)}bpm',
                        'intensity': f'{int(v + 0.5)}%',
                        'pace': f'{helper.velocity_to_pace(v, _to="mins/km")} /km'
                        }
                }
    except:
        return '--'

    return index[unit][metric]

def unpack(df, years, interval):
    res = dict.fromkeys([y for y in years])
    m = df.columns[0]

    for y in years:
        for mo in range(1, interval+1):# gets (year, month) key pairs
            if interval != 12: mo = '{:02}'.format(mo) # weeks indexed as strings
            try: # if (year, month) key exists append value
                val = df.loc[(y, mo), m]
            except:
                val = 0

            if res[y] == None:
               res[y] = [val]
            else:
                res[y].append(val)

    return res

def trend(df, interval, yr_range, unit):
    '''
    dte = dist, time, elev (sums)
    hip = HR, intensity, pace (averages)
    '''
    UNIT = unit

    def table(df):
        table = {'year': [],
                 'ytd': [],
                 'avg': [],
                 'max': [],
                 'min': []}
        metric = df.columns[0]
        df.dropna(axis=0)

        for y in yr_range:
            table['year'].append(y)
            if metric in ['dist', 'time', 'elev']:
                table['ytd'].append(convert(df.loc[y].sum()[0], metric, UNIT))
            else:
                table['ytd'].append('--')

            table['avg'].append(convert(df.loc[y].mean()[0], metric, UNIT))
            table['max'].append(convert(df.loc[y].max()[0], metric, UNIT))
            table['min'].append(convert(df.loc[y].min()[0], metric, UNIT))

        table = pd.DataFrame(table)
        table = table.to_html(index=False, escape=False)
        table = table[table.find('<tbody>'):table.find('</tbody>')]
        table = table.replace('<td>', '<td style="padding-right: 10px;padding-left: 10px;">')

        return table

    '''
    Manipulate data frames
    '''
    index = list(range(1, interval + 1))
    m = df.columns[0] # gets metric name
    table = table(df)
    df = unpack(df, yr_range, interval)

    '''
    Create figure objects
    '''
    fig = go.Figure()

    # Bars
    for y in yr_range:
        colors = list(map(lambda v, c : c.format('1') if v > 0 else 'rgba(0,0,0,0)', df[y], [COLORS[f'run{y%4}']]*len(index)))

        bar = go.Bar(
                name=f'<b>{y}</b>',
                x=index,
                y=df[y],
                width=1,
                visible=(y == list(yr_range)[-1]),
                marker=dict(
                        line=dict(
                                width=2,
                                color=colors #COLORS[f'run{y%7}'].format('1'),
                                ),
                        color=COLORS[f'run{y%7}'].format('.3')
                ),
                hoverinfo='text',
                hovertext=[f'<b>{y}<br>{convert(v, m, UNIT)}</b>' for v in df[y]],
                showlegend=True
                )
        fig.add_trace(bar)

        line = go.Scatter(
                name = y,
                x=[.5]+index+[interval+.5],
                y=[df[y][0]]+df[y]+[df[y][-1]],
                mode='lines',
                line=dict(
                        width=2,
                        shape='spline',
                        smoothing=.8,
                        color=COLORS[f'run{y%7}'].format('.5'),
                        simplify=False
                        ),
                fill='tozeroy',
                fillcolor=COLORS[f'run{y%7}'].format('.1'),
                hoverinfo='skip',
                hovertext=['-'] + [f'<b>{y}<br>{convert(v, m, UNIT)}</b>' for v in df[y]],
                visible=(y == list(yr_range)[-1]),
                showlegend=False
                )
        fig.add_trace(line)

    '''
    Update Layout
    '''
    if interval == 12:
        ticks = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    else:
        ticks = list(str(i+1) for i in range(interval))

    all_vals = [b for sub in df.values() for b in sub]
    if m == 'intensity':
        a = np.array(all_vals)
        miny = np.min(a[np.nonzero(a)]) * .9
    else:
        miny = (0.9*min(i for i in all_vals if i > 0)) * int(m in ('pace', 'avg_hr'))
    maxy =  1.05*max(all_vals)
    yrange = [miny, maxy]
    if m == 'pace' or m == 'avg_hr':
        yticks = np.linspace(miny, maxy, 4)
    else:
        yticks = np.linspace(miny, maxy, 8)
    yticktext = [f'<b>{convert(v, m, UNIT)}</b>' for v in yticks]

    yaxis = dict(
           domain=[0,.925],
           range=[miny, maxy],
           ticks='outside',
           tickangle=-90,
           tickmode='array',
           tickvals=yticks,
           ticktext=yticktext,
           showgrid=True,
           gridcolor=COLORS['gray'],
           layer='below traces',
           visible=True,
           )

    fig.update_layout(
            width=760,
            height=500,
            paper_bgcolor='white',
            plot_bgcolor='white',
            hovermode='x',
            margin=dict(
                    l=25,r=0,t=0,b=25,
                    autoexpand=False
                    ),
            barmode='overlay',
            showlegend=True,
            xaxis=dict(
                    type='linear',
                    tickmode='array',
                    tickvals=list(i+1 for i in range(interval)),
                    ticktext=[f'<b>{t}</b>' for t in ticks],
                    ),
            yaxis=yaxis,
            legend=dict(
                    itemclick='toggle',
                    itemdoubleclick='toggleothers',
                    x=1,
                    xanchor='right',
                    y=1,
                    yanchor='top'
                    )
            )

    '''
    Buttons
    '''
    available_years = list(y for y in yr_range)
    year_buttons = []

    for i in range(len(available_years)):
        year_buttons.append(dict(
                args=[{'visible': [False, False]*i + [True, True]*(len(available_years) - i)}],
                label=f'<b>{available_years[i]}</b>',
                method='restyle'
                ))

    fig.update_layout(
            updatemenus=[dict(
                    direction='down',
                    buttons=year_buttons,
                    pad={"r": 0, "t": 0},
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=0.875,
                    xanchor="right",
                    y=1,
                    yanchor="top",
                    active=len(available_years) - 1
                    ),
            dict(
                    direction='down',
                    buttons=[dict(
                            args=[{'width': [1]*len(available_years),
                                   'stackgroup': ['']*(len(available_years)),
                                   'fill': ['tozeroy']*len(available_years)},
                                   {'barmode': 'overlay',
                                   'yaxis.autorange': False,
                                   'yaxis.range': yrange,
                                   'yaxis.ticks': 'outside',
                                   'yaxis.showticklabels': True,
                                   'yaxis.showgrid': True},
                                    ],
                            label='<b>Overlay</b>',
                            method='update'
                            ),
                    dict(
                            args=[{'width': [1/(len(available_years)*2)]*len(available_years),
                                   'stackgroup': ['']*len(available_years),
                                   'fill': ['tozeroy']*len(available_years)},
                                    {'barmode': 'group',
                                   'yaxis.autorange': False,
                                   'yaxis.range': yrange,
                                   'yaxis.ticks': 'outside',
                                   'yaxis.showticklabels': True,
                                   'yaxis.showgrid': True}],
                            label='<b>Group</b>',
                            method='update'
                            ),
                    dict(
                            args=[{'width': [1]*len(available_years),
                                   'stackgroup': ['one']*len(available_years),
                                   'fill': ['tonexty']*len(available_years)},
                                   {'barmode': 'stack',
                                   'yaxis.autorange': True,
                                   'yaxis.ticks': '',
                                   'yaxis.showticklabels': False,
                                   'yaxis.showgrid': False}],
                            label='<b>Stack</b>',
                            method='update'
                            )],
                    pad={"r": 0, "t": 0},
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=0.77,
                    xanchor="right",
                    y=1,
                    yanchor="top",
                    active=0
                    ),
            dict(
                    direction='down',
                    buttons=[dict(
                            args=[{'visible': [True, False]*len(available_years),
                                   'hoverinfo': ['text','skip']*len(available_years),
                                   'showlegend': [True, False]*len(available_years)}],
                            args2=[{'visible': [False, False]*len(available_years),
                                    'showlegend': [False,
                                                   False]*len(available_years)}],
                            label='<b>All Bars</b>',
                            method='restyle'
                            ),
                            dict(
                            args=[{'visible': [False, True]*len(available_years),
                                   'hoverinfo': ['skip','text']*len(available_years),
                                   'showlegend': [False, True]*len(available_years)}],
                            args2=[{'visible': [False, False]*len(available_years),
                                    'showlegend': [False,
                                                  False]*len(available_years)}],
                            label='<b>All Lines</b>',
                            method='restyle'
                            ),
                            dict(
                            args=[{'visible': [True, True]*len(available_years),
                                   'hoverinfo':['text','skip']*len(available_years)}],
                            args2=[{'visible': [False, False]*len(available_years)}],
                            label='<b>Both</b>',
                            method='restyle'
                            )],
                    pad={"r": 0, "t": 0},
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=0.635,
                    xanchor="right",
                    y=1,
                    yanchor="top",
                    active=0
                    )
                ]
            )

    return fig, table

def mega_box(df, metric, unit):
    if unit == 'imperial':
        c = ('mi', 'ft')
    else:
        c = ('km', 'm')

    '''
    Stat Crunch
    '''
    min_yr, max_yr = min(df['date'].dt.year), max(df['date'].dt.year)
    df_yr = dict.fromkeys(list(range(min_yr, max_yr + 1)))
    for y in range(min_yr, max_yr + 1):
        df_yr[y] = list(df[df['date'].dt.year == y][metric])

    if metric in ['dist', 'time', 'pace', 'elev']:
        df = convert_frame(df[metric], metric, unit)
        for y in range(min_yr, max_yr + 1):
           df_yr[y] = convert_frame(df_yr[y], metric, unit)
    else:
        df = df[metric]

    '''
    Create Figure
    '''
    fig = go.Figure()

    fig.add_trace(go.Box(
            name='All Years',
            x=df,
            boxmean=True,
            hoveron='boxes',
            boxpoints='outliers',
            ))


    for y in range(min_yr, max_yr + 1):
        fig.add_trace(go.Box(
                name=str(y),
                x=df_yr[y],
                boxmean=True,
                hoveron='boxes',
                boxpoints='outliers',
                ))

    '''
    Update Layout
    '''
    _format = {
            'time': {
                    'type': 'date',
                    'format': '%H:%M:%S',
                    'suffix': '',
                    'autorange': True
                    },
            'pace': {
                    'type': 'date',
                    'format': '%M:%S',
                    'suffix': f' /{c[0]}',
                    'autorange': 'reversed'
                    },
            'dist': {
                    'type': '-',
                    'format': '.2f',
                    'suffix': f' {c[0]}',
                    'autorange': True
                    },
            'elev': {
                    'type': '-',
                    'format': ',.0f',
                    'suffix': f' {c[1]}',
                    'autorange': True
                    },
            'avg_hr': {
                    'type': '-',
                    'format': '.0f',
                    'suffix': ' bpm',
                    'autorange': True
                    },
            'intensity': {
                    'type': '-',
                    'format': '.0f',
                    'suffix': '%',
                    'autorange': True
                    },
            }

    fig.update_layout(
            autosize=True,
            margin=dict(l=0,r=0,t=0,b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            bargroupgap=0.1,
            yaxis=dict(
                    type='category',
                    ticksuffix=''
                    ),
            xaxis=dict(
                    type=_format[metric]['type'],
                    autorange=_format[metric]['autorange'],
                    tickmode='auto',
                    nticks=15,
                    tickformat=_format[metric]['format'],
                    ticksuffix =_format[metric]['suffix'],
                    ticks='outside',
                    tickson='boundaries'
                    )
            )

    return fig

def mega_hist(df, metric, unit):
    if unit == 'imperial':
        c = ('mi', 'ft')
    else:
        c = ('km', 'm')

    '''
    Stat Crunch
    '''
    min_yr, max_yr = min(df['date'].dt.year), max(df['date'].dt.year)
    df_yr = dict.fromkeys(list(range(min_yr, max_yr + 1)))
    for y in range(min_yr, max_yr + 1):
        df_yr[y] = list(df[df['date'].dt.year == y][metric])

    if metric in ['dist', 'time', 'pace', 'elev']:
        df = convert_frame(df[metric], metric, unit)
        for y in range(min_yr, max_yr + 1):
           df_yr[y] = convert_frame(df_yr[y], metric, unit)
    else:
        df = df[metric]

    '''
    Create Figure
    '''
    fig = go.Figure()

    fig.add_trace(go.Histogram(
            name='All Years',
            x=df,
            histnorm='percent',
            opacity=0.75,
            visible=True,
            showlegend=True,
            hoverinfo='name',
            marker=dict(
                    color='#696969'
                    )
            ))

    for y in range(min_yr, max_yr + 1):
        fig.add_trace(go.Histogram(
                name=str(y),
                x=df_yr[y],
                histnorm='percent',
                hoverinfo='name',
                visible='legendonly',
                marker=dict(
                        color=COLORS[f'run{y%7}'].format('.4')
                        )
                ))

    #fig = ff.create_distplot([df] + [df_yr[y] for y in df_yr], ['All'] + [str(y) for y in df_yr], show_rug=False, histnorm='probability')

    '''
    Update Layout
    '''
    _format = {
            'time': {
                    'type': 'date',
                    'format': '%H:%M:%S',
                    'suffix': '',
                    'autorange': True
                    },
            'pace': {
                    'type': 'date',
                    'format': '%M:%S',
                    'suffix': f' /{c[0]}',
                    'autorange': 'reversed'
                    },
            'dist': {
                    'type': '-',
                    'format': '.2f',
                    'suffix': f' {c[0]}',
                    'autorange': True
                    },
            'elev': {
                    'type': '-',
                    'format': ',.0f',
                    'suffix': f' {c[1]}',
                    'autorange': True
                    },
            'avg_hr': {
                    'type': '-',
                    'format': '.0f',
                    'suffix': ' bpm',
                    'autorange': True
                    },
            'intensity': {
                    'type': '-',
                    'format': '.0f',
                    'suffix': '%',
                    'autorange': True
                    },
            }

    fig.update_layout(
            width=1050,
            height=500,
            margin=dict(l=0,r=0,t=0,b=20, autoexpand=False),
            legend=dict(x=.9),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            bargap=0.01,
            bargroupgap=0.1,
            yaxis=dict(
                    type='category',
                    ticksuffix=''
                    ),
            xaxis=dict(
                    type=_format[metric]['type'],
                    autorange=_format[metric]['autorange'],
                    tickmode='auto',
                    nticks=15,
                    tickformat=_format[metric]['format'],
                    ticksuffix =_format[metric]['suffix'],
                    ticks='inside',
                    )
            )

    return fig