# -*- coding: utf-8 -*-
"""
@author: Spencer Ferguson-Dryden

Misc helper methods for Last7 app
"""
import stravalib
import os
from . import constants

STRAVA_CLIENT_ID = constants.STRAVA_CLIENT_ID
STRAVA_CLIENT_SECRET = os.environ['STRAVA_CLIENT_SECRET']
RAW_MAP = {8:r'\b', 7:r'\a', 12:r'\f', 10:r'\n', 13:r'\r', 9:r'\t', 11:r'\v'}

def auth_url(scope=''):
    _client = stravalib.Client()
    auth_url = _client.authorization_url(client_id=STRAVA_CLIENT_ID, redirect_uri='https://localhost', approval_prompt='force', scope = scope)
    return auth_url

def auth_token(code):
    _client = stravalib.Client()
    token = _client.exchange_code_for_token(client_id=STRAVA_CLIENT_ID, client_secret=STRAVA_CLIENT_SECRET, code=code)
    return token

def refresh_token(token):
    _client = stravalib.Client()
    refresh = _client.refresh_access_token(client_id=STRAVA_CLIENT_ID,  client_secret=STRAVA_CLIENT_SECRET, refresh_token=token)

    result = {
        'access_token': refresh['access_token'],
        'refresh_token': refresh['refresh_token'],
        'expires_at': refresh['expires_at']}

    return result

def pace(time, distance):
    pace = time/distance
    mm = int(pace//60)
    ss = '{:02}'.format(int(pace%60))
    return f'{mm}:{ss}'

def format_time(time):
    if time >= 3600:
        hh = f'{int(time//3600)}:'
    else:
        hh = ''
    mm = '{:02}'.format(int(time) % 3600 // 60)
    ss = '{:02}'.format(int(time%60))
    return f'{hh}{mm}:{ss}'

def velocity_to_pace(velocity, _from='m/s', _to='mins/mile'):
    if _from=='m/s' and _to=='mins/mile':
        try:
            return format_time(1/((velocity/1000)*0.6214))
        except ZeroDivisionError:
            return '0:00'
        except ValueError:
            return ''
    elif _from == 'm/s' and _to == 'mins/km':
        try:
            return format_time(1/(velocity/1000))
        except ZeroDivisionError:
            return '0:00'
        except ValueError:
            return ''

def pace_to_velocity(pace, _from='mins/mile', _to='m/s'):
    seconds = pace.split(':')
    if len(seconds) > 2:
        seconds = 3600*int(seconds[0]) + 60*int(seconds[1]) + int(seconds[2])
    else:
        seconds = 60*int(seconds[0]) + int(seconds[1])

    if _to=='m/s' and _from=='mins/mile':
        try:
            return 1609.344/seconds
        except ZeroDivisionError:
            return 0
        except ValueError:
            return 0
    elif _to == 'm/s' and _from == 'mins/km':
        try:
            return 1000/seconds
        except ZeroDivisionError:
            return 0
        except ValueError:
            return 0

def clean_stream(stream):
    import pandas as pd
    df = {**stream}
    df = pd.DataFrame(df, columns=list(stream.keys()))

    clean = df[df.moving.eq(True) & df.velocity.ge(.1)]
    return clean.to_dict(orient="list")

def get_laps(streams, laps):
    '''
    Returns a dict of dicts, with each index corresponding to a device lap.
    Each sub-dict contains streams for each data type from the input stream
    '''
    # Check of numLaps > 1
    if len(laps) <=1 :
        return {1: streams}

    result = {}

    for i in range(len(laps)):
        tmp = {}

        start = laps[i]['start_index']
        end = laps[i]['end_index']

        for k in streams:
            tmp[k] = streams[k][start:end+1]

        result[i+1] = tmp

    return result

def get_splits(streams, num_splits, unit):
    '''
    Gets auto splits (current miles) and remainder for the activity
    '''
    if unit == 'imperial':
        c = (1609.34, )
    else:
        c = (1000, )
    result = {}
    start = 0

    for i in range(1, num_splits):
        tmp = {}
        end = index_of_nearest(i*c[0], streams['dist'])

        for k in streams:
            tmp[k] = streams[k][start:end+1]
        result[i] = tmp
        start = end

    last_lap = {}
    for k in streams:
        last_lap[k] = streams[k][start:]
    if len(last_lap['dist']) > 4:
        result[num_splits] = last_lap

    return result

def convert_stream(stream, _from='m', _to='mi'):
    convert = {
            'm': {'mi': 0.000621371, 'ft': 3.28084, 'm': 1},
            'm/s': {'mile/min': 26.8224}
            }

    if _from == 'm':
        result = [s*convert[_from][_to] for s in stream]
    else:
        result = [convert[_from][_to]/s for s in stream]

    return result

def index_of_nearest(x, li):
    f = lambda list_value : abs(list_value - x)

    closest = min(li, key=f)

    return li.index(closest)

def format_activities(runs, athlete, flatten=True, activity_type='Run'):
    '''
    Takes client, filter dates, ids to keep, and activity type filter
    Returns a dict, with each key corresponding to a date and each value
    a list of dicts representing each run for that day
    {'2020-04-01': [{run1.keys: run1.values}, {run2.keys: run2.values()}]}

    if flatten == True, returns a flat list of dicts of each run
    '''
    from . import riegel
    from . import gap

    if flatten == False:
        result = {}
    else:
        result = []

    _polyline = r''

    for run in runs:
        # Convert each Activity Summary to type dict
        r = {}

        # skip if activity is not a run
        if run['type'] != 'Run' or run['type'] != 'Ride':
            continue

        # relabelling for convenience
        try:
            r['dist'] = int(round(run['distance']))
        except:
            r['dist'] = None
        try:
            r['elev'] = int(round(run['total_elevation_gain']))
        except:
            r['elev'] = None
        r['datetime'] = run['start_date_local'].replace('T', ' ')
        try:
            r['avg_hr'] = round(int(run['average_heartrate']))
        except:
            r['avg_hr'] = None
        r['start_lat'] = str(run['start_latitude'])
        r['start_lng'] = str(run['start_longitude'])
        r['achievement_count'] = run['achievement_count']
        r['kudos_count'] = run['kudos_count']

        # remove string-termination chars
        r['name'] = run['name'].replace('\'', ' ').replace('\"', ' ')

        # convert date to friendly format
        t = run['start_date_local']
        date = t[0:10] # gets set/compared to result dict key
        r['date'] = date

        # fix invalid time
        if run['moving_time'] == None:
            run['moving_time'] = 0

        # convert time to seconds
        r['time'] = run['moving_time']

        # Naive intensity, could improve w/ higher rate limit
        if r['time'] <= 0 or r['dist'] <= 0:
            r['intensity'] = 0
        else:
            velocity = r['dist']/r['time']
            intensity = riegel.riegel(athlete['pr_time'], athlete['pr_dist'],
                                      velocity, r['dist'])

            r['intensity'] = int(float(intensity[:intensity.find('%')])+.5)

        r['id'] = run['id'] # fix for stravalib compatibility

        polyline = run['map']['summary_polyline']
        if polyline != None:
            raw = r''.join(i if ord(i) > 32 else RAW_MAP.get(ord(i), i) for i in polyline)
            _polyline += raw + r','

        if flatten == False:
            if date in result.keys():
                result[date].append(r)
            else:
                result[date] = [r]
        else:
            result.append(r)

    return result, _polyline

def next_sunday(d, day=6):
    import datetime
    days_ahead = day - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        return d # return today
    return d + datetime.timedelta(days_ahead)

def hoverInfo(streams, unit, metric=None):
    df = {**streams}
    if unit == 'imperial':
        c = (.000621, 'mi', 'ft', 'mins/mile', 3.28084)
    else:
        c = (.001, 'km', 'm', 'mins/km', 1)

    distInfo = [round(d*c[0],2) for d in df['dist']]
    elevInfo = [int(round(e*c[-1], 0)) for e in df['elev']]
    paceInfo = [velocity_to_pace(v, _to=c[3]) for v in df['velocity']]
    gapInfo =  [velocity_to_pace(g, _to=c[3]) for g in df['gap']]
    gradeInfo =[int(round(g, 0)) for g in df['grade']]
    if metric == None:
        hoverInfo =[f'Dist: {distInfo[i]} {c[1]}<br>Pace: {paceInfo[i]} /{c[1]}<br>GAP: {gapInfo[i]} /{c[1]}<br>Elev: {elevInfo[i]} {c[2]}<br>Grade: {gradeInfo[i]}%' for i in      range(len(df['dist']))]
        return hoverInfo
    else:
        hoverInfo = {
                'dist': distInfo,
                'elev': elevInfo,
                'pace': paceInfo,
                'gap': gapInfo,
                'grade': gradeInfo
                }
        if metric == 'all':
            return hoverInfo
        else:
            return hoverInfo[metric]

def tickInfo(df, metric, space_list=[-5, -3, -2, -1, 0, 1, 2, 3, 5]):
    import statistics
    '''
    Tick Manipulations
    '''
    mean = statistics.mean(df[metric])
    stdev = statistics.stdev(df[metric])
    ticks = [mean+(i*stdev) for i in space_list]

    return ticks

def get_run_streams(client, activity_id):
    from . import gap

    raw_stream = client.get_activity_streams(activity_id,
                                         types=['distance',
                                                'velocity_smooth',
                                                'altitude',
                                                'grade_smooth',
                                                'moving',
                                                'latlng',
                                                'heartrate'])
    if raw_stream == None: # missing stream data
        return None

    try:
        dist=raw_stream['distance'].to_dict()['data']
        velocity=raw_stream['velocity_smooth'].to_dict()['data']
        moving=raw_stream['moving'].to_dict()['data']

        try:
            elev=raw_stream['altitude'].to_dict()['data']
            grade=raw_stream['grade_smooth'].to_dict()['data']
        except:
            elev=[0]*len(raw_stream['distance'].to_dict()['data'])
            grade=[0]*len(raw_stream['distance'].to_dict()['data'])

        try:
            latlng=raw_stream['latlng'].to_dict()['data']
        except:
            latlng=[[None,None]]*len(raw_stream['distance'].to_dict()['data'])

        try:
            hr=raw_stream['heartrate'].to_dict()['data']
        except:
            hr=[None]*len(raw_stream['distance'].to_dict()['data'])
    except:
        return None

    raw_stream=dict(
            dist=dist,
            velocity=velocity,
            moving=moving,
            elev=elev,
            grade=grade,
            latlng=latlng,
            hr=hr
            )

    GAP = gap.gap(raw_stream['velocity'],
                  raw_stream['grade'])

    raw_stream['gap'] = GAP

    cleaned = clean_stream(raw_stream)

    # Separate lat/lng into separate streams
    lat = [i[0] for i in cleaned['latlng']]
    lng = [i[1] for i in cleaned['latlng']]

    map_stream = {'lat': lat, 'lng': lng, 'elev': cleaned['elev'],
                  'dist': cleaned['dist'],
                  'velocity': cleaned['velocity'],
                  'gap': cleaned['gap'],
                  'grade': cleaned['grade']}

    return (raw_stream, cleaned, map_stream)

def run_stats(run, athlete, metric=None, streams=None):
    import datetime
    import statistics as stat
    from . import riegel
    from . import gap

    unit = athlete['unit']
    if unit == 'imperial':
        c = (0.000621371, 3.28084, 'mins/mile')
    else:
        c = (.001, 1, 'mins/km')

    try:
        hr = int(run['average_heartrate'])
    except:
        hr = ''

    try:
        v_mean = stat.mean(streams['velocity'])
        pace = velocity_to_pace(v_mean, _to=c[2])
        velocity = v_mean
        GAP = gap.gap(streams['velocity'], streams['grade'], out='p', unit=unit)
    except:
        pace = velocity_to_pace(run['average_speed'], _to=c[2])
        velocity = run['average_speed']
        GAP = pace

    try:
        intensity = riegel.riegel(athlete['pr_time'],
                              athlete['pr_dist'],
                              gap.gap(streams['velocity'], streams['grade'], out='v'),
                              int(run['distance']+0.5),
                              ret_type='html')
    except:
        if run['moving_time'] != None:
            intensity = riegel.riegel(athlete['pr_time'],
                                  athlete['pr_dist'],
      int(run['distance']+0.5)/(datetime.datetime.strptime(run['moving_time'], '%H:%M:%S')  - datetime.datetime.min).seconds,
      int(run['distance']+0.5), ret_type='html')
        else:
            intensity = ('','')

    intensity_pct = intensity[0]
    intensity_text = intensity[1]
    desc = run['description']
    if desc == None:
        desc = ''

    stats = {
            'name': run['name'],
            'distance': round(run['distance']*c[0], 2),
            'meters': run['distance'],
            'time': run['moving_time'],
            'seconds': sum([a*b for a,b in zip([3600,60,1],
                           map(int,run['moving_time'].split(':')))]),
            'elevation': round((run['total_elevation_gain']*c[1])),
            'pace': pace,
            'velocity': velocity,
            'gap': GAP,
            'intensity_pct': intensity_pct,
            'intensity_text': intensity_text,
            'avg_hr': hr,
            'dt': datetime.datetime.strptime(run['start_date_local'].replace('T', ' '), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S'),
            'date': datetime.datetime.strptime(run['start_date_local'].replace('T', ' '), '%Y-%m-%d %H:%M:%S').strftime('%a %d %b, %Y at %I:%M %p'),
            'desc': desc.replace('\n', '<br>'),
            'num_splits': int(round(run['distance']*c[0], 2) + 0.95),
            'laps': run['laps']
            }

    if metric == None:
        return stats
    else:
        return stats[metric]

def organize_dict(li, metric):
    # bugfix
    if type(li) == dict:
        try:
            li['velocity'] = li['dist']/li['time']
        except:
            li['velocity'] = 0
        if li['avg_hr'] == None:
            li['avg_hr'] = 0
        return {li['date'].strftime('%Y-%m-%d'): [li]}

    '''
    res = pd.DataFrame(li, columns=['date', 'dist', 'time', 'elev', 'avg_hr', 'kudos_count', 'achievement_count', 'intensity'])
    #res['date'] = pd.to_datetime(res['date'])
    res = res.groupby(res['date'])
    for i in res:
        print(i)
    print(res)
    '''
    result = {}

    for d in li:
        try:
            d['velocity'] = d['dist']/d['time']
        except:
            d['velocity'] = 0
        if d['avg_hr'] == None:
            d['avg_hr'] = 0
        try:
            key = d[metric].strftime('%Y-%m-%d')
        except:
            key = d[metric]
        if key in result.keys():
            result[key].append(d)
        else:
            result[key] = [d]

    return result

def format_dataframe(df, unit='imperial'):
    import pandas as pd

    # Conversion table
    convert = {
            'ft': 3.28084, 'mi': 0.000621371,
            'km': .001, 'm': 1
            }

    # Get lists of each column
    name, dist, time, pace, elev, activity_id = (list(df['name']), list(df['dist']), list(df['time']), list(df['pace']), list(df['elev']), list(df['activity_id']))

    ach, avhr, date, kud = (list(df['achievement_count']), list(df['avg_hr']), list(df['date']), list(df['kudos_count'])) # No operations on these

    # Format name
    name = [f'<a href="{activity_id[i]}"><div style="height:100%;width:100%">{name[i]}</div></a>' for i in range(len(name))]

    # Format time
    time = [format_time(t) for t in time]

    # Format HR
    avhr = ['' if pd.isna(hr) else int(hr) for hr in avhr]

    if unit == 'imperial':
        # Format dist
        dist = [f"{round(d*convert['mi'], 2)} mi" for d in dist]

        # Format elev
        elev = [f"{int(e*convert['ft'] + 0.5)} ft" for e in elev]

        # Format pace
        pace = [f'{velocity_to_pace(p)} /mi' for p in pace]

        # Reassemble dataframe
        df = pd.DataFrame(list(zip(date, name, dist, time, pace, elev, avhr, ach, kud)), columns=['Date', 'Name', 'Distance (mi)', 'Time', 'Pace (min/mile)', 'Elev (ft)', 'Avg HR', 'Achievement Count', 'Kudos Count'])
    else:
        # Format dist
        dist = [f"{round(d*convert['km'], 2)} km" for d in dist]

        # Format elev
        elev = [f"{int(e*convert['m'] + 0.5)} m" for e in elev]

        # Format pace
        pace = [f"{velocity_to_pace(p, _from='m/s', _to='mins/km')} /km" for p in pace]

        # Reassemble dataframe
        df = pd.DataFrame(list(zip(date, name, dist, time, pace, elev, avhr, ach, kud)), columns=['Date', 'Name', 'Distance (km)', 'Time', 'Pace (min/km)', 'Elev (m)',  'Avg HR', 'Achievement Count', 'Kudos Count'])

    return df

def weather(dt, lat, lng, unit):
    import requests
    import json
    import datetime

    coco = {
        1:  'Clear',
        2:	'Fair',
        3:	'Cloudy',
        4:	'Overcast',
        5:	'Fog',
        6:	'Freezing Fog',
        7:	'Light Rain',
        8:	'Rain',
        9:	'Heavy Rain',
        10:	'Freezing Rain',
        11:	'Heavy Freezing Rain',
        12:	'Sleet',
        13:	'Heavy Sleet',
        14:	'Light Snowfall',
        15:	'Snowfall',
        16:	'Heavy Snowfall',
        17:	'Rain Shower',
        18:	'Heavy Rain Shower',
        19:	'Sleet Shower',
        20:	'Heavy Sleet Shower',
        21:	'Snow Shower',
        22:	'Heavy Snow Shower',
        23:	'Lightning',
        24:	'Hail',
        25:	'Thunderstorm',
        26:	'Heavy Thunderstorm',
        27:	'Storm'
        }
    bearings = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'N']

    date = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    api_key = os.environ['METEOSTAT_KEY']
    header = {'x-api-key': api_key}
    query_station = f"https://api.meteostat.net/v2/stations/nearby?lat={lat}&lon={lng}&limit=10"

    stations = json.loads(requests.get(query_station, headers=header).text)['data']
    nearest_station_id = None

    for s in stations:
        if s['active'] == True:
            nearest_station_id = s['id']
            break
    if nearest_station_id == None:
        return ''

    query_weather = f"https://api.meteostat.net/v2/stations/hourly?station={nearest_station_id}&start={date}&end={date}"

    weather = json.loads(requests.get(query_weather, headers=header).text)['data']
    hour = int(datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S').hour)

    for w in weather:
        if datetime.datetime.strptime(w['time'], '%Y-%m-%d %H:%M:%S').hour == hour:
            break

    res = ''

    if w['coco'] != None:
        res += coco[w['coco']] + '<br>'

    if w['temp'] != None:
        if unit == 'imperial':
            w['temp'] = int(round(float(w['temp']*(9/5)) + 32))
            res += 'Temp: ' + str(w['temp']) + u' \N{DEGREE SIGN}F' + '<br>'
        else:
            res += 'Temp: ' + str(w['temp']) + u' \N{DEGREE SIGN}C' + '<br>'

    if w['prcp'] != None:
        if unit == 'imperial':
            w['prcp'] = round(w['prcp']*0.0393701, 2)
            res += 'Precip: ' + str(w['prcp']) + ' in<br>'
        else:
            res += 'Precip: ' + str(w['prcp']) + ' mm<br>'

    if w['snow'] != None:
        if unit == 'imperial':
            w['snow'] = round(w['snow']*0.0393701, 2)
            res += 'Snow: ' + str(w['snow']) + ' in<br>'
        else:
            res += 'Snow: ' + str(w['snow']) + ' mm<br>'

    if w['wspd'] != None:
        if unit == 'imperial':
            w['wspd'] = int(round(w['wspd']*0.621371))
            if w['wdir'] != None:
                wdir = f" (from {bearings[int((w['wdir']-22.5)%360)//45]}) "
            else: wdir = ''
            if w['wpgt'] != None:
                w['wpgt'] = int(round(w['wpgt']*0.621371))
                wpgt = f" (Peak: {w['wpgt']} mph)"
            else: wpgt = ''
            res += 'Wind: ' + str(w['wspd']) + f' mph{wdir}{wpgt}<br>'
        else:
            if w['wdir'] != None:
                wdir = f" (from {bearings[int((w['wdir']-22.5)%360)//45]}) "
            else: wdir = ''
            if w['wpgt'] != None:
                wpgt = f" (Peak: {w['wpgt']} km/h)"
            else: wpgt = ''
            res += 'Wind: ' + str(w['wspd']) + f' km/h{wdir}{wpgt}<br>'

    if w['rhum'] != None:
        res += f"Humidity: {w['rhum']}%"

    return res
