# -*- coding: utf-8 -*-
"""
Created on Fri May 22 12:24:26 2020

@author: sferg
"""
def riegel(pr_time, pr_distance, velocity, distance, ret_type=str, easy_pace=True):
    '''
    :param pr_time: time, in seconds, of the PR effort
    :param pr_distance: distance, in meters, of the PR effort
    :param time: time of the incoming run
    :param distance: distance of the incoming run

    ALL METRIC (METERS, SECONDS)

    :returns a curve of the athlete's equivalent best performances
    '''

    s1 = pr_distance/pr_time
    d1 = pr_distance

    if easy_pace:
        easy_pace = 2.06 # 13:00 min/mile #((s1) * ((d1/1609.34)**0.07))/2.25
    else:
        easy_pace=0

    velocity = velocity - easy_pace
    pr_effort = (s1 * ((d1/distance)**0.07)) - easy_pace
    pct = round((velocity/pr_effort) * 100, 2)
    effort = effort_zone(pct)

    if ret_type==str:
        return f'{pct}% ({effort})'
    elif ret_type=='html':
        return [f'{pct}%', effort]
    else:
        return pct

def effort_zone(pct):
    pct *= 2

    if pct > 200:
        return 'PR Effort'
    elif pct > 190:
        return 'Race/Anaerobic'
    elif pct > 180:
        return 'VO2 Max'
    elif pct > 160:
        return 'Tempo'
    elif pct > 140:
        return 'Threshold'
    elif pct > 115:
        return 'Endurance - Hard'
    elif pct > 85:
        return 'Endurance - Moderate'
    elif pct > 60:
        return 'Endurance - Easy'
    else:
        return 'Recovery'

def easy_velocity(pr_time, pr_distance):
    s1 = pr_distance/pr_time
    d1 = pr_distance

    easy_speed = ((s1) * ((d1/1609.34)**0.07))/2.25
    return easy_speed

def pr_velocity(pr_time, pr_distance, distance):
    s1 = pr_distance/pr_time
    d1 = pr_distance

    pr_velocity = (s1 * ((d1/distance)**0.07))
    return pr_velocity
