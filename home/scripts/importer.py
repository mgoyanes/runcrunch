# -*- coding: utf-8 -*-
"""
Created on Thu Jun 18 13:09:47 2020

@author: sferg
"""
import os
import asyncio
import aiohttp
import datetime
import time
import io
import json
import random
import string
import psycopg2 as psy
from pgcopy import CopyManager

from activity_dashboard.dash_apps.finished_apps import driver
from scripts import postgres as db
from scripts import helper

async def asyncrange(count):
    for i in range(1, count):
        yield(i)

def copy_to_db(activities, athlete, conn, cursor, created_at):
    t0 = time.time()
    csv = io.StringIO()
    polyline = activities[1]
    print('POLYLINE LENGTH:', len(polyline))
    print('NUM RUNS:', len(activities[0]))

    for a in activities[0]:
        a = {k:str(v) if v != None else r'\N' for (k,v) in a.items()}
        csv.write(str(chr(31)).join([
                a['id'],
                str(athlete['a_id']),
                a['name'],
                a['date'],
                a['datetime'],
                str(int(a['dist'])),
                a['time'],
                a['elev'],
                a['avg_hr'],
                a['intensity'],
                a['achievement_count'],
                a['kudos_count'],
                a['start_lat'],
                a['start_lng'],
                r'\N' # shareable key
                ]) + '\n')
        a_date = datetime.datetime.strptime(a['date'], '%Y-%m-%d').date()
        if a_date < created_at:
            created_at = a_date
    print('FORMATTED IN:', time.time()-t0)
    db.UPDATE('athletes', where=f"a_id = {athlete['a_id']}",
              numCols=1, cols='strava_created', vals=f"'{created_at}'", conn=conn)
    conn.commit()

    # Insert runs
    staging = ''.join(random.choices(string.ascii_lowercase, k = 7))

    cursor.execute(f'''CREATE TABLE {staging}
                       AS TABLE activities
                       WITH NO DATA''') # create dummy table
    conn.commit()

    try:
        csv.seek(0)
        cursor.copy_from(csv, f'{staging}', sep=str(chr(31)))
        conn.commit()
        print('COPIED IN:', time.time()-t0)

        """sql = f'''
        INSERT INTO activities
        SELECT * FROM {staging}
        WHERE NOT EXISTS (
                SELECT activity_id
                FROM activities
                WHERE activities.activity_id = {staging}.activity_id
        )
        '''"""
        sql = f'''
        LOCK TABLE activities IN EXCLUSIVE MODE;

        INSERT INTO activities (activity_id, a_id, name, date, datetime, dist, time, elev, avg_hr, intensity, achievement_count, kudos_count, start_lat, start_lng, shareable_key)
        SELECT {staging}.activity_id, {staging}.a_id, {staging}.name, {staging}.date, {staging}.datetime, {staging}.dist, {staging}.time, {staging}.elev, {staging}.avg_hr, {staging}.intensity, {staging}.achievement_count, {staging}.kudos_count, {staging}.start_lat, {staging}.start_lng, {staging}.shareable_key
        FROM {staging}
        LEFT OUTER JOIN activities ON (activities.activity_id = {staging}.activity_id)
        WHERE activities.activity_id IS NULL;

        COMMIT;'''

        print(sql)
        cursor.execute(sql)
        conn.commit()
    except:
        print('IMPORT FAILED')
        cursor.close()
        conn.close()
        conn = psy.connect(os.environ['DATABASE_URL'])
        cursor = conn.cursor()
    finally:
        cursor.execute(f'DROP TABLE {staging}')
        conn.commit()
    print('ACTIVITIES UPLOADED IN:', time.time()-t0)

    mgr = CopyManager(conn, 'polylines', ('a_id', 'polyline'))
    try:
        mgr.copy([
                (athlete['a_id'], polyline)
                ])
    except: pass
    finally:
        conn.commit()

    print('Uploaded in:', time.time()-t0)

async def get_json(query, header, session):
    print('requesting:', query)
    response = await session.request('GET', url=query, headers=header)
    data = await response.json()
    if len(data) == 0:
        return None
    return data

async def get_runs(before, after, athlete, token, conn, cursor, created_at):
    t1 = time.time()
    before, after = int(before.timestamp()), int(after.timestamp())
    header = {'Authorization': f"Bearer {token}"}

    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(1, 11): # 2000 activities
            query = f'https://www.strava.com/api/v3/athlete/activities?before={before}&after={after}&page={i}&per_page=200'
            tasks.append(get_json(query, header, session))

        runs = []
        for coro in asyncio.as_completed(tasks):
            res = await coro
            if res == None:
                pass
            else:
                runs += res

        print('Gathered:', time.time()-t1)
        return runs

def import_runs(athlete):
    t0 = time.time()
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cursor = conn.cursor()
    created_at = athlete['strava_created']
    after = datetime.datetime.strptime('2009-01-01', '%Y-%m-%d')
    today = datetime.datetime.today()

    # Authenticate athlete
    token = driver.authenticate(athlete, return_token=True)

    runs = asyncio.run(get_runs(today, after, athlete, token, conn, cursor, created_at))

    activities = helper.format_activities(runs, athlete, activity_type='Run', flatten=True)
    print('Formatted:', time.time()-t0)

    # Upload to DB
    copy_to_db(activities, athlete, conn, cursor, created_at)

    print('End Upload:', time.time()-t0)
    conn.close()
    cursor.close()
    return