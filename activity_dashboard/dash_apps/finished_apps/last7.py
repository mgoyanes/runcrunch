from scripts import helper
from scripts import riegel

def distance(activities, unit='imperial'):
    distance = sum(i['dist'] for i in activities)

    if unit == None:
        return distance
    elif 'imperial' in unit:
        return f'{round((distance * 0.000621371), 2)} mi'
    elif unit == 'metric':
        return f'{round((distance / 1000), 2)} km'

def time(activities, unit='hh:mm:ss'):
    t = sum(t['time'] for t in activities)
    if unit == 'ss':
        return t
    else:
        secs = '{:02}'.format(t % 60)
        mins = '{:02}'.format(t % 3600 // 60)
        hrs = '{:02}'.format(t // 3600)

        return f'{hrs}:{mins}:{secs}'

def elev(activities, unit=None):
    elev = sum(i['elev'] for i in activities)

    if unit == None:
        return elev
    elif 'imperial' in unit:
        return f'{int(round(elev * 3.28084, 0))} ft'
    else:
        return f'{int(round(elev, 0))} m'

def hr(activities):
    count = 0
    hr = 0
    for a in activities:
        if a['avg_hr'] == None: #or a['avg_hr'] == 0:
            continue
        if a['avg_hr'] > 0:
            count += 1
        hr += a['avg_hr']

    if count == 0:
        return ''
    else:
        return int(round(hr/count, 0))

def last7(activities, unit):
    '''
    :param (client) stravalib client object
    :param (athlete_id) id of specified athlete
    :param (unit) preferred unit type of athlete
    :param (tier) whether the athlete has paid for Last7

    :return a string with the Last7 stats
    '''
    totals = {}
    if type(activities) is not list:
        activities = [activities]

    # Sum distance and convert to specified unit
    try:
        totals['dist'] = distance(activities, unit=unit)
    except:
        totals['dist'] = ''

    # Sum time and convert to HH:MM:SS format
    try:
        totals['time'] = time(activities)
    except:
        totals['time'] = ''

    # Calculate pace and convert to MM:SS
    try:
        velocity = distance(activities, unit=None)/time(activities, unit='ss')
        if unit == 'imperial':
            totals['pace'] = f"{helper.velocity_to_pace(velocity, _from='m/s', _to='mins/mile')} /mi"
        else:
            totals['pace'] = f"{helper.velocity_to_pace(velocity, _from='m/s', _to='mins/km')} /km"
    except:
        totals['pace'] = ''

    # Sum elevation and convert to feet/meters
    try:
        totals['elev'] = elev(activities, unit=unit)
    except:
        totals['elev'] = ''

    # Calculate average intensity
    try:
        intensity = sum(i['intensity'] for i in activities)/len(activities)
        intensity = f'{int(intensity + 0.5)}% | {riegel.effort_zone(intensity)}'
        totals['intensity'] = intensity
    except:
        totals['intensity'] = ''

    # Calculate avg HR
    try:
        totals['avg_hr'] = hr(activities)
    except:
        totals['avg_hr'] = ''

    return totals
