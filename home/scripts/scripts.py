import os
import stravalib
import datetime
import psycopg2 as psy
import pandas as pd

from activity_dashboard.dash_apps.finished_apps import driver
from scripts import postgres as db
from scripts import helper

def account_totals(all_runs, athlete, unit):
    convert = {
            'imperial': [(0.000621371, 'mi'),
                         (3.28084, 'ft')],
            'metric': [(.001, 'km'),
                       (1, 'm')]
            }

    # Distance
    total_dist = all_runs['dist'].sum()
    dist = f'{"{:,}".format(int(total_dist * convert[unit][0][0] + 0.5))} {convert[unit][0][1]}'
    dist_fun = f'{round(total_dist/(40.075*10**6), 2)} times around the Earth!'

    # Time
    total_time = all_runs['time'].sum()
    time = helper.format_time(total_time)
    intervals = (
            ('weeks', 604800),  # 60 * 60 * 24 * 7
            ('days', 86400),    # 60 * 60 * 24
            ('hours', 3600),    # 60 * 60
            ('minutes', 60),
            ('seconds', 1),
            )

    def display_time(seconds, granularity=5):
        result = []

        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])
    time_fun = display_time(total_time)

    # Elevation
    total_elev = all_runs['elev'].sum()
    elev = f'{"{:,}".format(int(total_elev * convert[unit][1][0] + 0.5))} {convert[unit][1][1]}'
    elev_fun = f'{round(total_elev/8848, 2)} ascents of Mt. Everest!'

    # Activity count
    count = '{:,}'.format(all_runs['activity_id'].count())

    res = {'dist': dist,
            'dist_fun': dist_fun,
            'time': time,
            'time_fun': time_fun,
            'elev': elev,
            'elev_fun': elev_fun,
            'count': count,
            }

    return res