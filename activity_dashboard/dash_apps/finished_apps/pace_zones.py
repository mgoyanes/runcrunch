import plotly.graph_objects as go
import math
import pandas as pd
import numpy as np

from scripts import helper
from scripts import riegel
from scripts import constants

COLORS = constants.COLORS

async def zone_chart(streams, stats, athlete):
    if athlete['unit'] == 'imperial':
        c = (0.000621371, 'mi', 'mins/mile')
    else:
        c = (.001, 'km', 'mins/km')

    df_stream = {**streams}

    '''
    Data Crunch
    '''
    # Riegel info
    easy = riegel.easy_velocity(athlete['pr_time'], athlete['pr_dist'])
    pr = riegel.pr_velocity(athlete['pr_time'], athlete['pr_dist'], stats['meters']) - easy

    velocity = list(map(lambda v : v - easy, df_stream['velocity']))
    gap = list(map(lambda v : v - easy, df_stream['gap']))

    # Distribution vars
    labels = ['recovery', 'easy', 'moderate', 'hard', 'threshold', 'tempo', 'vo2', 'race', 'pr']
    bins = [-math.inf, .3*pr, .425*pr, .575*pr, .7*pr, .8*pr, .9*pr, .95*pr, pr, math.inf]

    # Make dataframe and cut into bins
    df = pd.DataFrame(list(zip(velocity, gap)), columns=['velocity', 'gap'])
    df['pace_zones'] = pd.cut(df['velocity'], bins=bins, labels=labels)
    df['gap_zones'] = pd.cut(df['gap'], bins=bins, labels=labels)
    counts_pace = df['pace_zones'].value_counts(normalize=True, sort=False)
    counts_gap = df['gap_zones'].value_counts(normalize=True, sort=False)

    '''
    Figure vars
    '''
    # Distribution values
    values_pace = [
            counts_pace.sum(), # Base
            # Recovery parent/leaf
            counts_pace['recovery'], #counts_pace['recovery'],
            # Endurance parent
            counts_pace['easy'] + counts_pace['moderate'] + counts_pace['hard'],
            # Endurance leaves
            counts_pace['easy'], counts_pace['moderate'], counts_pace['hard'],
            # Workout parent
            counts_pace['threshold'] + counts_pace['tempo'] + counts_pace['vo2'],
            # Workout leaves
            counts_pace['threshold'], counts_pace['tempo'], counts_pace['vo2'],
            # Race parent
            counts_pace['race'] + counts_pace['pr'],
            # Race leaves
            counts_pace['race'], counts_pace['pr']
            ]

    values_gap = [
            counts_gap.sum(), # Base
            # Recovery parent/leaf
            counts_gap['recovery'], #counts_gap['recovery'],
            # Endurance parent
            counts_gap['easy'] + counts_gap['moderate'] + counts_gap['hard'],
            # Endurance leaves
            counts_gap['easy'], counts_gap['moderate'], counts_gap['hard'],
            # Workout parent
            counts_gap['threshold'] + counts_gap['tempo'] + counts_gap['vo2'],
            # Workout leaves
            counts_gap['threshold'], counts_gap['tempo'], counts_gap['vo2'],
            # Race parent
            counts_gap['race'] + counts_gap['pr'],
            # Race leaves
            counts_gap['race'], counts_gap['pr']
            ]

    paces = [f'< {helper.velocity_to_pace(bins[1]+easy, _to=c[2])} /{c[1]}'] + [f'{helper.velocity_to_pace(bins[i]+easy, _to=c[2])} /{c[1]} - {helper.velocity_to_pace(bins[i-1]+easy, _to=c[2])} /{c[1]}' for i in range(2,9)] + [f'> {helper.velocity_to_pace(bins[-2]+easy, _to=c[2])} /{c[1]}']

    # Sector colors
    colors = ['rgb(255,255,255)',
          '#5c5c5c', #'#5c5c5c',
          '#3ed6d6', "#75acff", "#6de3db", "#3dd44c",
          '#e8b417', "#f5e616", "#f29624", "#fa0c0c",
          '#fc0dec', '#fc0dec', '#fc0dec'
          ]

    # Hovertext 0 = recovery, 1 = easy, 2 = moderate, 3 = hard, 4 = threshold,
    # 5 = tempo, 6 = vo2, 7 = race, 8 = pr
    pct_pace = list(map(lambda p : int(round(float(p)*100)), counts_pace))
    tm_pace = list(map(lambda p : int(round(float(p)*float(stats['seconds']))), counts_pace))
    dist_pace = list(map(lambda p : int(round(float(p)*float(stats['meters']))), counts_pace))
    zipped_pace = list(map(lambda pz, p, t, d: f"{pz}<br><b>{p}%<br>{helper.format_time(t)}<br>{round(d*c[0],2)} {c[1]}</b>", paces, pct_pace, tm_pace, dist_pace))

    hovertext_pace = [
            '',
            zipped_pace[0], #zipped_pace[0],
            f'<b>{pct_pace[1] + pct_pace[2] + pct_pace[3]}%<br>{helper.format_time(tm_pace[1]+tm_pace[2]+tm_pace[3])}<br>{round((dist_pace[1]+dist_pace[2]+dist_pace[3])*c[0],2)} {c[1]}</b>',
            zipped_pace[1], zipped_pace[2], zipped_pace[3],
            f'<b>{pct_pace[4] + pct_pace[5] + pct_pace[6]}%<br>{helper.format_time(tm_pace[4]+tm_pace[5]+tm_pace[6])}<br>{round((dist_pace[4]+dist_pace[5]+dist_pace[6])*c[0],2)} {c[1]}</b>',
            zipped_pace[4], zipped_pace[5], zipped_pace[6],
            f'<b>{pct_pace[7] + pct_pace[8]}%<br>{helper.format_time(tm_pace[7]+tm_pace[8])}<br>{round((dist_pace[7]+dist_pace[8])*c[0],2)} {c[1]}</b>',
            zipped_pace[7], zipped_pace[8]
            ]

    pct_gap = list(map(lambda p : int(round(float(p)*100)), counts_gap))
    tm_gap = list(map(lambda p : int(round(float(p)*float(stats['seconds']))), counts_gap))
    dist_gap = list(map(lambda p : int(round(float(p)*float(stats['meters']))), counts_gap))
    zipped_gap = list(map(lambda pz, p, t, d: f'{pz}<br><b>{p}%<br>{helper.format_time(t)}<br>{round(d*c[0],2)} {c[1]}</b>',paces, pct_gap, tm_gap, dist_gap))

    hovertext_gap = [
            '',
            zipped_gap[0], #zipped_gap[0],
            f'<b>{pct_gap[1] + pct_gap[2] + pct_gap[3]}%<br>{helper.format_time(tm_gap[1]+tm_gap[2]+tm_gap[3])}<br>{round((dist_gap[1]+dist_gap[2]+dist_gap[3])*c[0],2)} {c[1]}</b>',
            zipped_gap[1], zipped_gap[2], zipped_gap[3],
            f'<b>{pct_gap[4] + pct_gap[5] + pct_gap[6]}%<br>{helper.format_time(tm_gap[4]+tm_gap[5]+tm_gap[6])}<br>{round((dist_gap[4]+dist_gap[5]+dist_gap[6])*c[0],2)} {c[1]}</b>',
            zipped_gap[4], zipped_gap[5], zipped_gap[6],
            f'<b>{pct_gap[7] + pct_gap[8]}%<br>{helper.format_time(tm_gap[7]+tm_gap[8])}<br>{round((dist_gap[7]+dist_gap[8])*c[0],2)} {c[1]}</b>',
            zipped_gap[7], zipped_gap[8]
            ]

    '''
    Create Figure
    '''
    fig = go.Figure()

    # Root text
    base = '<b>Pace Zones</b>'

    fig.add_trace(go.Sunburst( # Pace
            name='Pace Zones',
            ids=[base,
                'Recovery', #'Recovery - leaf',
                'Endurance', 'Easy', 'Moderate', 'Hard',
                'Workout', 'Threshold', 'Tempo', 'VO2 Max',
                'Race', 'Race/Anaerobic', 'PR Effort'
                ],
            labels=[base,
                    'Recovery', #'Recovery',
                    'Endurance', 'Easy', 'Moderate', 'Hard',
                    'Workout', 'Threshold', 'Tempo', 'VO2 Max',
                    'Race', 'Race', 'PR Effort'
                    ],
            parents=['',
                     base, #'Recovery',
                     base, 'Endurance', 'Endurance', 'Endurance',
                     base, 'Workout', 'Workout', 'Workout',
                     base, 'Race', 'Race'
                     ],
            values=values_pace,
            marker=dict(
                    colors=colors,
                    line=dict(width=1.5)
                    ),
            leaf=dict(
                    opacity=1
                    ),
            branchvalues='total',
            hovertext=hovertext_pace,
            hoverinfo='label+text',
            insidetextorientation='auto',
            domain=dict(column=0)
            ))

    # Root text
    base = '<b>GAP Zones</b>'

    fig.add_trace(go.Sunburst( # GAP
            name='GAP Zones',
            ids=[base,
                'Recovery', #'Recovery - leaf',
                'Endurance', 'Easy', 'Moderate', 'Hard',
                'Workout', 'Threshold', 'Tempo', 'VO2 Max',
                'Race', 'Race/Anaerobic', 'PR Effort'
                ],
            labels=[base,
                    'Recovery', #'Recovery',
                    'Endurance', 'Easy', 'Moderate', 'Hard',
                    'Workout', 'Threshold', 'Tempo', 'VO2 Max',
                    'Race', 'Race', 'PR Effort'
                    ],
            parents=['',
                     base, #'Recovery',
                     base, 'Endurance', 'Endurance', 'Endurance',
                     base, 'Workout', 'Workout', 'Workout',
                     base, 'Race', 'Race'
                     ],
            values=values_gap,
            marker=dict(
                    colors=colors,
                    line=dict(width=1.5)
                    ),
            leaf=dict(
                    opacity=1
                    ),
            branchvalues='total',
            hovertext=hovertext_gap,
            hoverinfo='label+text',
            insidetextorientation='auto',
            domain=dict(column=1)
            ))

    '''
    Update Layout
    '''
    fig.update_layout(
            grid=dict(columns=2, rows=1),
            margin=dict(t=0, l=0, r=0, b=15),
            height=450,
            width=1100,
            )

    return fig.to_html(include_plotlyjs='cdn', include_mathjax='cdn', full_html=False,
                       config=dict(displayModeBar=False)), 'g5'

async def grades(streams, stats, athlete):
    if athlete['unit'] == 'imperial':
        c = (0.000621371, 'mi', 'mins/mile')
    else:
        c = (.001, 'km', 'mins/km')

    '''
    Create Distribution
    '''
    df = pd.DataFrame(streams, columns=['grade'])
    df['grade'] = list(map(lambda g : int(g), df['grade']))
    x = [i for i in range(min(df['grade']), max(df['grade']))]
    df['bins'] = pd.cut(df['grade'], bins=[-math.inf]+x, labels=[str(i) for i in x])
    df = df['bins'].value_counts(normalize=True, sort=False)

    '''
    Create Figure
    '''
    fig = go.Figure()

    hovertext = list(map(lambda g, b : '{:+d}%'.format(g) + f"<b><br>Freq: {round(b*100, 2)}%<br>{round(b*stats['meters']*c[0],2)} {c[1]}", x, df))

    fig.add_trace(go.Bar(
            x=x,
            y=df,
            marker=dict(
                    color=x,
                    colorscale=constants.GRADE_SCALE_HIST,
                    cmid=0,
                    cmin=-25,
                    cmax=25,
                    showscale=False,
                    opacity=.85,
                    line=dict(
                            color=COLORS['blueT'].format('1'),
                            width=2
                            )
                    ),
            width=1,
            hoverinfo='text',
            hovertext=hovertext
            ))

    '''
    Update Layout
    '''
    ceil = (math.ceil(max(list(df))*10)*10)/100
    ticks = np.arange(0, ceil, ceil/10)

    fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            width=1024,
            height=450,
            margin=dict(l=0,r=0,t=0,b=0),
            xaxis=dict(
                    tickformat='+f',
                    ticksuffix='%',
                    nticks=7
                    ),
            yaxis=dict(
                    tickmode='array',
                    tickvals=ticks,
                    ticktext=[f'{int(round(i*100))}%' for i in ticks],
                    gridcolor=COLORS['gray'],
                    showgrid=True,
                    ticks=''
                    )
            )

    return fig.to_html(include_plotlyjs='cdn', include_mathjax='cdn', full_html=False,
                       config=dict(displayModeBar=False)), 'g6'

def grades_pace_contour(streams, stats):
    '''
    Create Figrue
    '''
    fig = go.Figure()

    fig.add_trace(go.Histogram2dContour(
            y=streams['gap'],
            x=streams['grade'],
            ybins=dict(start=0),
            histnorm='percent',
            colorscale='Blues'
            ))

    return fig