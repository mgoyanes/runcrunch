from scripts import postgres as db
import psycopg2 as psy
import stravalib
import os

RAW_MAP = {8:r'\b', 7:r'\a', 12:r'\f', 10:r'\n', 13:r'\r', 9:r'\t', 11:r'\v'}

'''
New activity
'''
def new_activity(a_id, activity_id):
    # Retrieve info from DB
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    athlete = db.SELECT('athletes', where=f"a_id = {a_id}", conn=conn)

    # Get run details
    client = authenticate(athlete)
    run = client.get_activity(activity_id=activity_id)

    # skip if activity is not a run
    if run.type not in ['Run', 'Ride', 'Walk', 'Hike', 'Apline Ski', 'Nordic Ski']:
        return

    # Parse run info
    run_info = parse_run(run, athlete)

    # Parse polyline
    polyline = run.map.summary_polyline
    if polyline != None:
        raw = r''.join(i if ord(i) > 32 else RAW_MAP.get(ord(i), i) for i in polyline)
        cur = conn.cursor()
        sql = f"UPDATE polylines SET polyline = polyline || '" + raw + f",' WHERE a_id = {athlete['a_id']}"

        try:
            cur.execute(sql)
            print(sql)
            conn.commit()
        except:
            print('FAILED:', sql)
            conn.close()
            conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')

    db.INSERT('activities', run_info, conn=conn)
    conn.close()

    return

'''
Changed Title
'''
def update_title(activity_id, title):
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')

    # Update DB with new title
    db.UPDATE('activities', where=f"activity_id = {activity_id}", numCols=1,
              cols='name', vals=f"'{title}'", conn=conn)
    conn.close()

    return

'''
Deleted activity
'''
def delete_activity(activity_id):
    db.DELETE('activities', where=f'activity_id = {activity_id}')
    return

'''
Deauthorized app
'''
def deauthorize(a_id):
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')

    # Get username
    user = db.SELECT('athletes', where=f'a_id = {a_id}', conn=conn)['username']

    # Delete auth_user
    try:
        db.DELETE('auth_user', where=f"username = '{user}'")
    except: # All Auth user
        cur = conn.cursor()
        cur.execute(f"SELECT id FROM auth_user WHERE username = '{user}'")
        user_id = cur.fetchone()[0]
        cur.close()
        db.DELETE('socialaccount_socialaccount', where=f"user_id = {user_id}")
        db.DELETE('auth_user', where=f"username = '{user}'")

    conn.close()
    return

'''
Helper methods
'''
def parse_run(run, athlete):
    from scripts import riegel
    import datetime

    info = {}
    run_dict = run.to_dict()

    info['id'] = run.id

    info['a_id'] = athlete['a_id']

    info['name'] = '\''+ run.name[:100].replace('\'', ' ').replace('\"', ' ') + '\''

    info['date'] = run.start_date_local.strftime('\'%Y-%m-%d\'')

    info['datetime'] = run.start_date_local.strftime('\'%Y-%m-%d %H:%M:%S\'')

    info['dist'] = int(run_dict['distance'] + 0.5)

    if run.moving_time == None:
        info['time'] = 0
    else:
        info['time'] = run.moving_time.seconds

    info['elev'] = int(run_dict['total_elevation_gain'] + 0.5)

    info['avg_hr'] = run.average_heartrate

    try:
        velocity = info['dist']/info['time']
        intensity = riegel.riegel(athlete['pr_time'], athlete['pr_dist'], velocity, info['dist'])
        info['intensity'] = int(float(intensity[:intensity.find('%')])+.5)
    except:
        info['intensity'] = 0

    info['achievement_count'] = run.achievement_count

    info['kudos_count'] = run.kudos_count

    info['start_lat'] = "'" + str(run.start_latitude) + "'"

    info['start_lng'] = "'" + str(run.start_longitude) + "'"

    info['shareable_key'] = 'NULL'

    # Format query string
    query = ', '.join(list(map(lambda x : str(x), info.values())))
    query = query.replace('None', 'NULL').replace("'None'", 'NULL')

    return query

def authenticate(athlete):
    import time

    access_token = athlete['access_token']

    if time.time() > athlete['expires_at'] - 100:
        try:
            codes = refresh_token(athlete['refresh_token'])
        except:
            pass

        db.UPDATE('athletes', where=f"a_id = {athlete['a_id']}",
                  numCols=3, cols="access_token, refresh_token, expires_at",
                  vals=f"'{codes['access_token']}', '{codes['refresh_token']}',     {codes['expires_at']}")

        access_token = codes['access_token']

    try:
        client = stravalib.Client(access_token=access_token)
    except:
        return None

    return client

def refresh_token(token):
    _client = stravalib.Client()
    refresh = _client.refresh_access_token(client_id=os.environ['STRAVA_CLIENT_ID'],
                                           client_secret=os.environ['STRAVA_CLIENT_SECRET'],
                                           refresh_token=token)

    result = {
        'access_token': refresh['access_token'],
        'refresh_token': refresh['refresh_token'],
        'expires_at': refresh['expires_at']}
    return result

if __name__ == '__main__':
    import sys
    a_id = sys.argv[1]
    activity_id = sys.argv[2]

    new_activity(a_id, activity_id)