# -*- coding: utf-8 -*-
"""
Created on Fri May 29 18:15:24 2020

@author: sferg
"""
import plotly.graph_objects as go
import statistics as stat
import numpy as np
import os

from scripts import helper
from scripts import riegel
from scripts import constants

COLORS = constants.COLORS
INTENSITYSCALE = constants.INTENSITYSCALE_LINE[::2]
INTENSITYSCALE.append(constants.INTENSITYSCALE_LINE[-1])
MAPBOX_TOKEN = os.environ['MAPBOX_TOKEN']

def getBoundsZoomLevel(bounds, mapDim):
    """
    source: https://stackoverflow.com/questions/6048975/google-maps-v3-how-to-calculate-the-zoom-level-for-a-given-bounds
    :param bounds: list of ne and sw lat/lon
    :param mapDim: dictionary with image size in pixels
    :return: zoom level to fit bounds in the visible area
    """
    ne_lat = bounds[0]
    ne_long = bounds[1]
    sw_lat = bounds[2]
    sw_long = bounds[3]

    scale = 2 # adjustment to reflect MapBox base tiles are 512x512 vs. Google's 256x256
    WORLD_DIM = {'height': 256 * scale, 'width': 256 * scale}
    ZOOM_MAX = 18

    def latRad(lat):
        sin = np.sin(lat * np.pi / 180)
        radX2 = np.log((1 + sin) / (1 - sin)) / 2
        return max(min(radX2, np.pi), -np.pi) / 2

    def zoom(mapPx, worldPx, fraction):
        return np.floor(np.log(mapPx / worldPx / fraction) / np.log(2))

    latFraction = (latRad(ne_lat) - latRad(sw_lat)) / np.pi

    lngDiff = ne_long - sw_long
    lngFraction = ((lngDiff + 360) if lngDiff < 0 else lngDiff) / 360

    latZoom = zoom(mapDim['height'], WORLD_DIM['height'], latFraction)
    lngZoom = zoom(mapDim['width'], WORLD_DIM['width'], lngFraction)

    return min(latZoom, lngZoom, ZOOM_MAX)

async def map_pic(streams):

    fig = go.Figure()

    # Main Map Trace
    fig.add_trace(go.Scattermapbox(
            lat=streams['lat'],
            lon=streams['lng'],
            mode='lines',
            line=dict(
                    color=COLORS['red'],
                    width=4
                    )
            ))

    bounds = [max(streams['lat']), max(streams['lng']), min(streams['lat']), min(streams['lng'])]
    mapDim = {'height': 170, 'width': 200}

    fig.update_layout(
            height=187,
            width=232,
            margin=dict(
                    pad=0,
                    l=0,
                    r=0,
                    t=0,
                    b=0,
                    autoexpand=False
                    ),
            mapbox=dict(
                    bearing=0,
                    center=go.layout.mapbox.Center(
                            lat=stat.mean(streams['lat']),
                            lon=stat.mean(streams['lng'])
                            ),
                    pitch=0,
                    zoom=getBoundsZoomLevel(bounds, mapDim)
                    ),
            mapbox_style='outdoors',
            mapbox_accesstoken=MAPBOX_TOKEN,
            showlegend=False
            )

    return fig.to_html(include_plotlyjs='cdn', full_html=False,
                       config=dict(displayModeBar=False, staticPlot=True)), 'g7'

async def profile3D(streams, stats, athlete):

    if athlete['unit'] == 'imperial':
        c = (1609.34, 3.28084, 'mi', 'ft', 'mins/mile')
    else:
        c = (1000, 1, 'km', 'm', 'mins/km')

    df = {**streams}
    df['elev'] = list(map(lambda x : x*c[1], df['elev']))

    '''
    Pace Zone Colorbar
    '''
    PR_TIME = athlete['pr_time']
    PR_DISTANCE = athlete['pr_dist']
    pr = riegel.pr_velocity(PR_TIME, PR_DISTANCE, stats['meters'])
    easy = riegel.easy_velocity(PR_TIME, PR_DISTANCE)
    pace_zones = dict(
                    width=10,
                    color=df['velocity'],
                    cmin=easy,
                    cmax=pr,
                    showscale=True,
                    colorscale=INTENSITYSCALE,
                    colorbar=dict(
                            thickness=15,
                            x=0,
                            y=.5,
                            tickfont=dict(size=8),
                            tickangle=0,
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
                                      'VO2 Max',
                                      'Race',
                                      ],
                            )
                    )

    gap_zones = dict(
                    width=10,
                    color=df['gap'],
                    cmin=easy,
                    cmax=pr,
                    showscale=True,
                    colorscale=INTENSITYSCALE,
                    colorbar=dict(
                            thickness=15,
                            x=0,
                            y=.5,
                            tickfont=dict(size=8),
                            tickangle=0,
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
                                      'VO2 Max',
                                      'Race',
                                      ],
                            )
                    )

    grade_zones = dict(
            width=10,
            color=df['grade'],
            cmax=max(10, max(max(df['grade']), abs(min(df['grade'])))),
            cmin=min(-10, min(min(df['grade']), -1*max(df['grade']))),
            cmid=0,
            showscale=True,
            colorscale=constants.GRADE_SCALE,
            reversescale=False,
            colorbar=dict(
                    thickness=15,
                    x=0,
                    y=.5,
                    tickfont=dict(size=8),
                    tickangle=0,
                    )
            )

    default_line = dict(
            width=10,
            color=COLORS['red']
            )

    '''
    Create figure objects
    '''
    fig = go.Figure()

    profile = go.Scatter3d(
            y=df['lat'],
            x=df['lng'],
            z=df['elev'],
            mode='lines',
            line=default_line,
            hoverinfo='text',
            hovertext=helper.hoverInfo(streams, athlete['unit']),
            projection=dict(
                    y=dict(show=True),
                    x=dict(show=True)
            ),
            surfaceaxis=-1, # bugged
            surfacecolor=COLORS['transparentGray']
        )

    '''
    Draw Traces
    '''
    fig.add_trace(profile)

    '''
    Update Layout
    '''
    max_elev = max(df['elev'])
    min_elev = min(df['elev'])

    if max_elev - min_elev > 200:
        max_z = max_elev + 100
    elif max_elev - min_elev > 50:
        max_z = max_elev + 25
    else:
        max_z = max_elev + (max_elev-min_elev) * 5


    if min_elev < 0:
        min_z = min_elev
    elif min_elev < 100:
        min_z = 0
    else:
        min_z = min_elev - 100

    if athlete['unit'] == 'imperial':
        suffix = 'ft'
    else:
        suffix = 'm'

    fig.update_layout(
            autosize=True,
            margin=dict(
                    pad=0,
                    l=0,
                    r=0,
                    t=0,
                    b=0,
                    autoexpand=False,
                    ),
            scene_camera=dict(
                    eye=dict(
                            x=3, y=3, z=0.1
                            )
                    ),
                    scene=dict(
                            xaxis=dict(
                                    title="",
                                    visible=True,
                                    backgroundcolor=COLORS['transparent'],
                                    showgrid=False,
                                    showticklabels=False,
                                    ticks="",
                                    mirror=True
                                    ),
                            yaxis=dict(
                                    title="",
                                    visible=True,
                                    backgroundcolor=COLORS['transparent'],
                                    showgrid=False,
                                    showticklabels=False,
                                    ticks="",
                                    mirror=True
                                    ),
                            zaxis=dict(
                                    range=[min_z, max_z],
                                    backgroundcolor=COLORS['transparent'],
                                    title="<b>Elevation</b>",
                                    showgrid=True,
                                    gridcolor='black',
                                    gridwidth=.5,
                                    ticks='',
                                    ticksuffix = suffix,
                                    showticksuffix='last',
                                    mirror=True
                            )
                    ),
            scene_aspectmode='manual',
            scene_aspectratio=dict(x=100*(max(df['lng'])-min(df['lng'])),
                                   y=125*(max(df['lat'])-min(df['lat'])),
                                   z=1)
            )

    '''
    Add Buttons
    '''
    fig.update_layout(
            updatemenus=[dict(
                    type='buttons',
                    direction='left',
                    buttons=list([
                            dict(   args2=['line', pace_zones],
                                    args=['line', default_line],
                                    label='<b>Toggle Pace Zones</b>',
                                    method='restyle'
                                    )
                            ]),
                    visible=True,
                    pad={"r": 10, "t": 1},
                    bgcolor=COLORS['gray1'],
                    bordercolor=COLORS['blue'],
                    borderwidth=1.5,
                    showactive=True,
                    x=.075,
                    xanchor="left",
                    y=0.9,
                    yanchor="bottom"), dict(
                    type='buttons',
                    direction='left',
                    buttons=list([
                            dict(   args2=['line', grade_zones],
                                    args=['line', default_line],
                                    label='<b>Toggle Grades</b>',
                                    method='restyle'
                                    )
                            ]),
                    pad={"r": 10, "t": 1},
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=.39,
                    xanchor="left",
                    y=0.9,
                    yanchor="bottom"), dict(
                    type='buttons',
                    direction='left',
                    buttons=list([
                            dict(   args2=['line', gap_zones],
                                    args=['line', default_line],
                                    label='<b>Toggle Pace Zones (GAP)</b>',
                                    method='restyle'
                                    )
                            ]),
                    pad={"r": 10, "t": 1},
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=.215,
                    xanchor="left",
                    y=0.9,
                    yanchor="bottom")
                    ]
            )

    return fig.to_html(include_plotlyjs='cdn', include_mathjax='cdn', full_html=False,
                       config=dict(displayModeBar=False)), 'g1'

async def trace_map(streams, streams_laps, stats, athlete):

    if athlete['unit'] == 'imperial':
        c = (1609.34, 3.28084, 'mi', 'ft', 'mins/mile')
    else:
        c = (1000, 1, 'km', 'm', 'mins/km')

    df = {**streams}
    raw = {**streams_laps}

    '''
    Create Figure Objects
    '''
    fig = go.Figure()

    # Main Map Trace
    trace = go.Scattermapbox(
            lat=df['lat'],
            lon=df['lng'],
            mode='lines',
            line=dict(
                    color=COLORS['red'],
                    width=4
                    ),
            hoverinfo='text',
            hovertext=helper.hoverInfo(streams, unit=athlete['unit'])
            )

    # Auto Laps (mi/km) - INDEX 1
    auto_laps_indices = [helper.index_of_nearest(i*c[0], df['dist']) for i in range(1, int(stats['distance']) + 1)]
    auto_laps_lat = [str(df['lat'][i]) for i in auto_laps_indices]
    auto_laps_lng = [str(df['lng'][i]) for i in auto_laps_indices]

    auto_laps = go.Scattermapbox(
                lat=auto_laps_lat,
                lon=auto_laps_lng,
                mode='markers+text',
                text=[f'{i+1}' for i in range(len(auto_laps_indices))],
                textposition='top right',
                hoverinfo='text',
                marker=dict(
                        symbol='circle',
                        size=6,
                        color='black'
                        )
                )

    # Device Laps INDEX 2
    device_laps_indices = list(map(lambda x: x['start_index'], stats['laps']))[1:]
    device_laps_lat = [str(raw['latlng'][i][0]) for i in device_laps_indices]
    device_laps_lng = [str(raw['latlng'][i][1]) for i in device_laps_indices]

    try:
        device_laps = go.Scattermapbox(
                lat=device_laps_lat,
                lon=device_laps_lng,
                mode='markers+text',
                text=['Lap ' + str(i+1) for i in range(len(device_laps_indices))],
                textposition='top right',
                hoverinfo='text',
                opacity=1,
                marker=dict(
                        symbol='circle',
                        size=6,
                        color=COLORS['Recovery']
                        )
                )
    except:
        device_laps = go.Scattermapbox(
                lat=auto_laps_lat,
                lon=auto_laps_lng,
                mode='none',
                visible=False
                )


    # Highest/Lowest points INDEX 3, 4
    highest, lowest = df['elev'].index(max(df['elev'])), df['elev'].index(min(df['elev']))
    elev_hi_lat, elev_hi_lng = [str(df['lat'][highest])], [str(df['lng'][highest])]
    elev_lo_lat, elev_lo_lng = [str(df['lat'][lowest])], [str(df['lng'][lowest])]

    elev_hi = go.Scattermapbox(
            lat=elev_hi_lat,
            lon=elev_hi_lng,
            opacity=1,
            mode='markers+text',
            text=f'Highest Point<br>{int(max(df["elev"])*c[1]+.5)} {c[3]}',
            textposition='top right',
            hoverinfo='text',
            marker=dict(
                    opacity=1,
                    symbol='circle',
                    size=6,
                    color=COLORS['green']
                    )
            )
    elev_lo = go.Scattermapbox(
            lat=elev_lo_lat,
            lon=elev_lo_lng,
            opacity=1,
            mode='markers+text',
            text=f'Lowest Point<br>{int(min(df["elev"])*c[1]+.5)} {c[3]}',
            textposition='top right',
            hoverinfo='text',
            hoverlabel=dict(
                    bgcolor='rgba(255,255,255,.75)',
                    bordercolor=COLORS['red'],
                    ),
            marker=dict(
                    opacity=1,
                    symbol='circle',
                    size=6,
                    color=COLORS['gray']
                    )
            )

    # Fastest Points - INDEX 5,6
    fastest, fastest_gap = df['velocity'].index(max(df['velocity'])), df['gap'].index(max(df['gap']))
    fastest_lat, fastest_lng = [str(df['lat'][fastest])], [str(df['lng'][fastest])]
    fastest_gap_lat, fastest_gap_lng = [str(df['lat'][fastest_gap])], [str(df['lng'][fastest_gap])]

    fastest_point = go.Scattermapbox(
            lat=fastest_lat,
            lon=fastest_lng,
            opacity=1,
            mode='markers+text',
            text=f'Fastest Pace<br>{helper.velocity_to_pace(max(df["velocity"]), _to=c[-1])} /{c[2]}',
            textposition='top right',
            hoverinfo='text',
            marker=dict(
                    opacity=1,
                    symbol='circle',
                    size=6,
                    color=COLORS['Race']
                    )
            )
    fastest_gap_point = go.Scattermapbox(
            lat=fastest_gap_lat,
            lon=fastest_gap_lng,
            mode='markers+text',
            text=f'Fastest GAP<br>{helper.velocity_to_pace(max(df["gap"]), _to=c[-1])} /{c[2]}',
            textposition='top right',
            hoverinfo='text',
            opacity=1,
            marker=dict(
                    opacity=1,
                    symbol='circle',
                    size=6,
                    color=COLORS['orange']
                    )
            )

    '''
    Draw Figure
    '''
    fig.add_trace(trace) # 0 = main trace
    fig.add_trace(auto_laps) # 1 = auto laps
    fig.add_trace(device_laps) # 2 = device laps
    fig.add_trace(elev_hi) # 3
    fig.add_trace(elev_lo) # 4
    fig.add_trace(fastest_point) # 5
    fig.add_trace(fastest_gap_point) # 6

    '''
    Update Layout
    '''
    bounds = [max(df['lat']), max(df['lng']), min(df['lat']), min(df['lng'])]
    mapDim = {'height': 512, 'width': 450}

    fig.update_layout(
            autosize=True,
            margin=dict(
                    pad=0,
                    l=0,
                    r=0,
                    t=0,
                    b=0,
                    autoexpand=False
                    ),
            hovermode='closest',
            mapbox=dict(
                    bearing=0,
                    center=go.layout.mapbox.Center(
                            lat=stat.mean(df['lat']),
                            lon=stat.mean(df['lng'])
                            ),
                    pitch=0,
                    zoom=getBoundsZoomLevel(bounds, mapDim)
                    ),
            mapbox_style='outdoors',
            mapbox_accesstoken=MAPBOX_TOKEN,
            showlegend=False
            )

    '''
    Add Buttons
    '''
    fig.update_layout(
             updatemenus=[dict(
                    direction='down',
                    buttons=list([
                            dict(   args=['visible', [True]+[False]*6],
                                    label='<b>None</b>',
                                    method='restyle'
                            ),
                            dict(
                                    args=['visible', [True, True]+[False]*5],
                                    label='<b>Auto Splits</b>',
                                    method='restyle'
                           ),
                           dict(
                                   args=['visible', [True, False, True]+[False]*4],
                                   label='<b>Device Splits</b>',
                                   method='restyle'
                          ),
                           dict(
                                  args=['visible', [True]+[False]*2+[True]*4],
                                  label='<b>Min/Max</b>',
                                  method='restyle'
                              ),
                          dict(
                                  args=['visible', [True]*7],
                                  label='<b>All</b>',
                                  method='restyle'
                              )
                            ]),
                    active=4,
                    pad={"r": 0, "t": 0},
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=0.875,
                    xanchor="right",
                    y=0.9975,
                    yanchor="top"), dict(
                    direction='down',
                    buttons=list([
                            dict(   args=['mapbox.style', 'streets'],
                                    label='<b>Basic</b>',
                                    method='relayout'
                                    ),
                            dict(   args=['mapbox.style', 'outdoors'],
                                    label='<b>Topographic</b>',
                                    method='relayout'
                                    ),
                            dict(   args=['mapbox.style', 'satellite'],
                                    label='<b>Satellite</b>',
                                    method='relayout'
                                    ),
                            dict(   args=['mapbox.style', 'satellite-streets'],
                                    label='<b>Sat + Streets</b>',
                                    method='relayout'
                                    )
                            ]),
                    pad={"r": 10, "t": 1},
                    active=1,
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=1,
                    xanchor="right",
                    y=1,
                    yanchor="top")
                    ]
            )

    return fig.to_html(include_plotlyjs='cdn', include_mathjax='cdn', full_html=False,
                       config=dict(displayModeBar=False)), 'g0'

def global_heatmap(lat, lng):
    '''
    Create Figure
    '''
    fig = go.Figure()
    print(len(lat))
    if len(lat) > 500000:
        lat = lat[::3]
        lng = lng[::3]
    elif len(lat) > 200000:
        lat = lat[::2]
        lng = lng[::2]

    heatmap = go.Densitymapbox(
            lat=lat,
            lon=lng,
            zauto=True,
            radius=7,
            showlegend=False,
            colorscale='Plasma',
            below=""
            )

    fig.add_trace(heatmap)

    '''
    Update Layout
    '''
    fig.update_layout(
            autosize=False,
            width=1190,
            height=690,
            margin=dict(
                    pad=0,
                    l=0,
                    r=0,
                    t=0,
                    b=0,
                    autoexpand=False
                    ),
            hovermode=False,
            mapbox=dict(
                    bearing=0,
                    pitch=0,
                    zoom=0
                    ),
            mapbox_style='outdoors',
            mapbox_accesstoken=MAPBOX_TOKEN,
            showlegend=False
            )

    '''
    Buttons
    '''
    fig.update_layout(
            updatemenus=[dict(
                    direction='down',
                    buttons=list([
                            dict(   args=['mapbox.style', 'streets'],
                                    label='<b>Basic</b>',
                                    method='relayout'
                                    ),
                            dict(   args=['mapbox.style', 'outdoors'],
                                    label='<b>Topographic</b>',
                                    method='relayout'
                                    ),
                            dict(   args=['mapbox.style', 'satellite'],
                                    label='<b>Satellite</b>',
                                    method='relayout'
                                    ),
                            dict(   args=['mapbox.style', 'satellite-streets'],
                                    label='<b>Sat + Streets<b>',
                                    method='relayout'
                                    )
                            ]),
                    pad={"r": 0, "t": 0},
                    active=1,
                    bordercolor=COLORS['blue'],
                    bgcolor=COLORS['gray1'],
                    borderwidth=1.5,
                    showactive=True,
                    x=0.995,
                    xanchor='right',
                    y=1,
                    yanchor='top')
                    ]
            )

    return fig