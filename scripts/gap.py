# -*- coding: utf-8 -*-
"""
Created on Thu May 21 20:08:03 2020

@author: sferg
"""
from . import helper
import statistics

def gap_model(grade, elev):
    '''
    grade: a slope grade in %

    returns: a pace multiplier based on the input grade
    '''
    alt_adjust = 1.9/304.8 # 1.9% VO2 adjust per 1000 ft
    x = grade
    a = -0.00000328132
    b = 0.0014977
    c = 0.0303574
    d = 1
    if elev < 304.8:
        altitude = 0
    else:
        altitude = (alt_adjust*elev)/100
    if x == 0:
        return 1 + altitude  # normalize to zero
    else:
        multiplier = (a*(x**3) + b*(x**2) + c*x + d)

    return multiplier + altitude

def gap(velocity_stream, grade_stream, elev_stream, out='vs', unit='imperial'):
    gap_velocity = list(map(lambda g, v, e : gap_model(g, e)*v, grade_stream,
                            velocity_stream, elev_stream))

    if out=='vs':
        return gap_velocity
    elif out=='p':
        if unit == 'imperial':
           return helper.velocity_to_pace(sum(g for g in gap_velocity)/len(gap_velocity))
        else:
           return helper.velocity_to_pace(sum(g for g in gap_velocity)/len(gap_velocity), _to='mins/km')
    else:
        return statistics.mean(gap_velocity)

def splits_GAP(streams, num_splits, unit, laps=False):
    df = {**streams}

    if not laps:
        split_streams = helper.get_splits(df, num_splits, unit)
    else:
        split_streams = helper.get_laps(df, num_splits)

    splits = list(split_streams.keys()) # laps iterator

    s_paces = []
    s_GAPs = []
    s_elevs = []
    s_minelevs = []
    s_maxelevs = []
    s_totalgain = []
    s_dists = []
    s_avg_grades = []

    for s in splits:
        # Average pace of each lap
        s_avg_pace = statistics.mean(split_streams[s]['velocity'])
        s_paces.append(s_avg_pace)

        # Average gap of each lap
        s_gap_velocity = gap(split_streams[s]['velocity'], split_streams[s]['grade'],
                             elev_stream=split_streams[s]['elev'], out='vs')
        s_GAP = statistics.mean(s_gap_velocity)
        s_GAPs.append(s_GAP)

        # Elevation delta of each lap
        elev = int((split_streams[s]['elev'][-1]-split_streams[s]['elev'][0]))
        s_elevs.append(elev)

        # Min elev of each lap
        s_minelevs.append(int(min(split_streams[s]['elev'])))

        # Max elev of each lap
        s_maxelevs.append(int(max(split_streams[s]['elev'])))

        # Elevation gain of each lap
        elev_steps = list(map(lambda y,x : y-x, split_streams[s]['elev'][1:], split_streams[s]['elev'][0:-1]))
        s_totalgain.append(int(sum(list(filter(lambda x : x > 0, elev_steps)))))

        # Total distance of each lap
        dist = split_streams[s]['dist'][-1]-split_streams[s]['dist'][0]
        s_dists.append(dist)

        # Avg grade of each lap
        avg_grades = int(round(sum(split_streams[s]['grade'])/len(split_streams[s]['grade'])))
        s_avg_grades.append(avg_grades)

    return {'velocity': s_paces,
            'gap': s_GAPs,
            'elev': s_elevs,
            'dist': s_dists,
            'min_elev': s_minelevs,
            'max_elev': s_maxelevs,
            'total_gain': s_totalgain,
            'avg_grade': s_avg_grades}
