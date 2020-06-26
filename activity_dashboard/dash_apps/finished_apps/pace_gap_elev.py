# -*- coding: utf-8 -*-
"""
Created on Tue May 26 23:13:25 2020

@author: sferg
"""
import plotly.graph_objects as go
from scripts import helper
from scripts import riegel
from scripts import constants

COLORS = constants.COLORS
INTENSITYSCALE=[
        [0.0, '#5c5c5c'], # Recovery
         [.3, '#5c5c5c'],

          [.3, "#75acff"], # Easy
           [.425, "#75acff"],

            [.425, "#6de3db"], # Moderate
             [.575, "#6de3db"],

              [.575, "#3dd44c"], # Hard
               [.7, "#3dd44c"],

                [.7, "#f5e616"], # Threshold
                 [.8, "#f5e616"],

                  [.8, "#f29624"], # Tempo
                   [.9, "#f29624"],

                    [.9, "#fa0c0c"], # VO2 max
                     [.95, "#fa0c0c"],

                      [.95, "#fc0dec"],
                       [1.0, '#fc0dec'] # Race
            ]

INTENSITYSCALE_SMOOTH = INTENSITYSCALE[::2]
INTENSITYSCALE_SMOOTH.append(INTENSITYSCALE[-1])

async def pace_gap_elev_chart(streams, athlete):

    if athlete['unit'] == 'imperial':
        cs = (1609.34, 3.28084, 'mi', 'ft', 'mins/mile')
    else:
        cs = (1000, 1, 'km', 'm', 'mins/km')

    df = {**streams}
    df['elev'] = list(map(lambda x : x*cs[1], df['elev']))
    df['dist'] = list(map(lambda x : x*(1/cs[0]), df['dist']))

    '''
    Helper Vars
    '''
    hoverInfo = helper.hoverInfo(streams, athlete['unit'], metric='all')
    tickInfoPace = helper.tickInfo(df, 'velocity')
    tickInfoGAP = helper.tickInfo(df, 'gap')
    pr = riegel.pr_velocity(athlete['pr_time'], athlete['pr_dist'], df['total_distance'])
    easy = riegel.easy_velocity(athlete['pr_time'], athlete['pr_dist'])
    if athlete['unit'] == 'imperial':
        c = ('mi', 'ft', 'mins/mile')
    else:
        c = ('km', 'm', 'mins/km')
    gap_marker = dict(
                    size=6,
                    color=df['gap'],
                    cmin=easy,
                    cmax=pr,
                    showscale=False,
                    colorscale=INTENSITYSCALE,
                    colorbar=dict(
                            thickness=20,
                            tickfont=dict(size=10),
                            tickangle=-90,
                            tickmode='array',
                            tickvals=[easy, # min
                                      .5875*pr, # easy .65
                                      .68125*pr, # moderate .7125
                                      .75*pr, # hard .7875
                                      .81875*pr, # thresh .85
                                      .875*pr, # tempo .9
                                      .925*pr, # vo2 .95
                                      .9625*pr, # race .975
                                      .9875*pr], # max 1
                            ticktext=['',
                                      'Recovery',
                                      'Endurance<br>(Easy)',
                                      'Endurance<br>(Moderate)',
                                      'Endurance<br>(Hard)',
                                      'Threshold',
                                      'Tempo',
                                      'VO2<br>Max',
                                      'Race',
                                      ]
                            )
                    )
    pace_marker = dict(
                    size=6,
                    color=df['velocity'],
                    cmin=easy,
                    cmax=pr,
                    showscale=False,
                    colorscale=INTENSITYSCALE,
                    colorbar=dict(
                            thickness=20,
                            tickfont=dict(size=10),
                            tickangle=-90,
                            tickmode='array',
                            tickvals=[easy, # min
                                      .5875*pr, # easy .65
                                      .68125*pr, # moderate .7125
                                      .75*pr, # hard .7875
                                      .81875*pr, # thresh .85
                                      .875*pr, # tempo .9
                                      .925*pr, # vo2 .95
                                      .9625*pr, # race .975
                                      .9875*pr], # max 1
                            ticktext=['',
                                      'Recovery',
                                      'Endurance<br>(Easy)',
                                      'Endurance<br>(Moderate)',
                                      'Endurance<br>(Hard)',
                                      'Threshold',
                                      'Tempo',
                                      'VO2<br>Max',
                                      'Race',
                                      ]
                            )
            )

    '''
    Draw Figure
    '''
    elev_check = sum(df['elev']) > 1
    fig = go.Figure()
    fig.add_trace(go.Scatter( # Elev
            name='Elevation',
            x=df['dist'],
            y=df['elev'],
            fill='tozeroy',
            mode='lines',
            yaxis='y',
            visible=elev_check,
            showlegend=elev_check,
            line=dict(
                    shape='spline',
                    smoothing=1,
                    color=COLORS['green'],
                    simplify=True,
                    ),
            fillcolor=COLORS['greenT'].format('.3'),
            hoverinfo='x+text',
            hovertext=list(map(lambda e, g: f'<b>Elev: {e} {c[1]}<br>Grade: {g}%</b>',
                               hoverInfo['elev'], hoverInfo['grade']))
            )
        )

    fig.add_trace(go.Scatter( # Pace
            name='Pace',
            x=df['dist'],
            y=df['velocity'],
            yaxis='y2',
            mode='lines',
            opacity=0.65,
            line=dict(
                    width=2,
                    shape='spline',
                    smoothing=1.1,
                    color=COLORS['blue'],
                    simplify=True
                    ),
            hoverinfo='x+text',
            hovertext=list(map(lambda p: f'<b>Pace: {p} /{c[0]}</b>', hoverInfo['pace']))
            )
        )
    fig.add_trace(go.Scatter( # GAP
            name='GAP',
            x=df['dist'],
            y=df['gap'],
            yaxis='y2',
            mode='lines',
            opacity=0.65,
            fill='tonexty',
            line=dict(
                    width=2,
                    shape='spline',
                    smoothing=1.1,
                    color=COLORS['orange'],
                    simplify=True
                    ),
            hoverinfo='x+text',
            hovertext=list(map(lambda g: f'<b>GAP: {g} /{c[0]}</b>', hoverInfo['gap'])),
            visible=elev_check,
            showlegend=elev_check,
            )
        )
    if df['hr'][0] != None:
        fig.add_trace(go.Scatter( # HR
                name='HR',
                x=df['dist'],
                y=df['hr'],
                yaxis='y3',
                mode='lines',
                opacity=0.65,
                line=dict(
                        width=2,
                        shape='spline',
                        smoothing=1.1,
                        color=COLORS['red'],
                        simplify=True
                        ),
                hoverinfo='x+text',
                hovertext=list(map(lambda h : f'<b>{int(h+0.5)} bpm</b>', df['hr'])),
                visible=True
                )
            )

    '''
    Axis Settings
    '''
    max_elev = max(df['elev'])
    min_elev = min(df['elev'])
    range_pace = [min(tickInfoPace[1], tickInfoGAP[1]), max(tickInfoPace[-2], tickInfoGAP[-2])]

    fig.update_layout(
            xaxis =dict(
                    domain=[0,1],
                    zeroline=False,
                    showgrid=False,
                    ticks='inside',
                    ticksuffix=f' {c[0]}',
                    showticksuffix='all',
                    tickcolor=COLORS['text'],
                    hoverformat='.2r',
                    ),
            # Elevation
            yaxis =dict(
                    domain=[0,1],
                    range=[min_elev-10, max_elev*1.01],
                    side='right',
                    zeroline=False,
                    showgrid=False,
                    ticks='outside',
                    ticksuffix=c[1],
                    showticksuffix='first',
                    tickcolor=COLORS['text'],
                    visible=elev_check
                    ),
            # Pace
            yaxis2=dict(
                    domain=[0,1],
                    range=range_pace,
                    side='left',
                    zeroline=False,
                    overlaying='y',
                    gridwidth=1,
                    gridcolor=COLORS['blue'],
                    showgrid=False,
                    tickvals=tickInfoPace,
                    ticktext=[f'{helper.velocity_to_pace(v, _to=c[-1])} /{c[0]}' for v in tickInfoPace],
                    ticks='outside',
                    tickcolor=COLORS['text'],
                    visible=True
                    ),
            yaxis3=dict(
                    domain=[0,1],
                    autorange=True,
                    side='right',
                    zeroline=False,
                    overlaying='y',
                    gridwidth=1,
                    gridcolor=COLORS['red'],
                    showgrid=False,
                    ticks='outside',
                    ticksuffix='bpm',
                    showticksuffix='last',
                    tickcolor=COLORS['text'],
                    visible=False
                    )
            )

    '''
    Aesthetic Settings
    '''
    max_elev = max(df['elev'])
    if max_elev < 10:
        rpad = 55
    elif max_elev < 1000:
        rpad = 60
    elif max_elev < 10000:
        rpad = 65
    else:
        rpad = 70

    fig.update_layout(
            plot_bgcolor=COLORS['transparent'],
            paper_bgcolor=COLORS['transparent'],
            width=1110,
            height=450,
            margin=dict(
                    pad=0,
                    l=175,
                    r=rpad,
                    t=0,
                    b=15,
                    autoexpand=False
                    ),
            font=dict(
                    color=COLORS['text']
                    ),
            hovermode='x unified',
            hoverlabel=dict(
                    bgcolor=COLORS['whiteT'].format('.75'),
                    namelength=0
                    ),
            showlegend=True,
            legend=dict(
                    itemclick='toggle',
                    itemdoubleclick='toggleothers',
                    x=-.2,
                    xanchor='left',
                    y=1,
                    yanchor='top'
                    )
            )

    '''
    Show/Hide Buttons
    '''
    fig.update_layout(
            updatemenus=[dict( # Grid Visibility
                        direction='right',
                        buttons=list([
                            dict(
                                args=[{'xaxis.showgrid': False,
                                       'yaxis.showgrid': False,
                                       'yaxis2.showgrid': False,
                                       'yaxis3.showgrid': False,
                                       'xaxis.visible': False,
                                       'yaxis.visible': False,
                                       'yaxis2.visible': False,
                                       'yaxis3.visible': False}],
                                label="None",
                                method="relayout"
                            ),
                            dict(
                                args=[{'yaxis3.showgrid': True,
                                       'yaxis3.visible': True}],
                                label="HR",
                                method="relayout"
                            ),
                            dict(
                                args=[{'yaxis.showgrid': True,
                                       'yaxis.visible': True}],
                                label="Elev",
                                method="relayout"
                            ),
                            dict(
                                args=[{'yaxis2.showgrid': True,
                                      'yaxis2.visible': True}],
                                label="Pace",
                                method="relayout"
                            ),
                            dict(
                                args=[{'xaxis.showgrid': True,
                                       'yaxis.showgrid': True,
                                       'yaxis2.showgrid': True,
                                       'yaxis3.showgrid': True,
                                       'xaxis.visible': True,
                                       'yaxis.visible': True,
                                       'yaxis2.visible': True,
                                       'yaxis3.visible': True}],
                                label="All",
                                method="relayout"
                            ),
                    ]),
                    active=4,
                    pad={"r": 0, "t": 0},
                    bgcolor=COLORS['gray1'],
                    bordercolor=COLORS['blue'],
                    borderwidth=1.5,
                    showactive=True,
                    x=-.175,
                    xanchor="left",
                    y=0.65,
                    yanchor="top"
                ),
            dict( # Pace/GAP Line mode
                    direction='right',
                    buttons=list([
                            dict(
                            args=[{'stackgroup': ['', '', '', ''],
                                   'yaxis': ['y', 'y2', 'y2', 'y3']},
                                  {'yaxis2.autorange': False,
                                   'yaxis2.range': range_pace,
                                   'yaxis2.visible': True,
                                   'yaxis3.visible': True}
                                  ],
                            label='Overlay',
                            method='update'
                            ),
                            dict(
                            args=[{'stackgroup': ['', 'one', 'one', ''],
                                   'yaxis': ['y', 'y2', 'y2', 'y3']},
                                  {'yaxis2.autorange': True,
                                   'yaxis2.visible': False,
                                   'yaxis3.visible': False}],
                            label='Stack',
                            method='update'
                            )
                    ]),
                    pad={"r": 10, "t": 10},
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    active=0,
                    x=-0.19,
                    xanchor="left",
                    y=.55,
                    yanchor="top"
                    ),
            dict( # GAP to Markers
                    type='buttons',
                    direction='left',
                    buttons=list([dict(
                            args2=[{'mode': ['none', 'markers', 'markers', 'lines'],
                                    'marker': [None, pace_marker, gap_marker, None]}],
                            args=[{'mode': ['none', 'lines', 'lines', 'lines']}],
                            label='Pace Zones',
                            method='update'
                            )]),
                    pad={"r": 1, "t": 10},
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=-0.195,
                    xanchor="left",
                    y=.42,
                    yanchor="top"
                    ),
        ]
    )

    return fig.to_html(include_plotlyjs='cdn', include_mathjax='cdn', full_html=False,
                       config=dict(displayModeBar=False)), 'g2'