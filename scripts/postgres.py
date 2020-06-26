# -*- coding: utf-8 -*-
"""
Database Python script for Strava Last7 app
"""
import psycopg2 as psy
import os

def COPY(table, file, conn=None):
    if conn == None:
        conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()



    conn.commit()
    cur.close()

    return

def INSERT(table, vals, conn=None):
    '''
    :param (table) table to insert into
    :param (vals) values to insert

    Throws exception if table requirements not met
    '''
    # CONNECT TO DATABASE
    if conn == None:
        conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()

    # ADD TO DATABASE
    if type(vals) == list:
        for v in vals:
            sql = f'''INSERT INTO {table} VALUES ({v})'''
            print(sql)
            try:
                cur.execute(sql)
            except:
                print('SQL INSERT ERROR')
                cur.close()
                conn.commit()
                conn.close()
                conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
                cur = conn.cursor()
                continue
    else:
        try:
            sql = f'''INSERT INTO {table} VALUES ({vals})'''
            print(sql)
        except:
            print('SQL INSERT ERROR')
            conn.commit()
            cur.close()
            return

        cur.execute(sql)
        conn.commit()

    print('SQL INSERTED SUCCESSFULLY')

    conn.commit()
    cur.close()

    return

def UPDATE(table, where, numCols, cols, vals, conn=None):
    '''
    :params (table) the table to update
    :params (a_id) the row to update
    :params (numCols) the number of columns to update
    :params (cols) the names of columns to update
    :params (vals) list of values to insert

    Throws error if table requirements not met
    '''
    # CONNECT TO DATABASE
    if conn == None:
        conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()

    # PERFORM UPDATE AND COMMIT
    if numCols > 1:
        sql = f'''UPDATE {table} SET ({cols}) = ({vals}) WHERE {where}'''
    else:
        sql = f'''UPDATE {table} SET {cols} = {vals} WHERE {where}'''

    print(sql)

    try:
        cur.execute(sql)
        conn.commit()
        print('SQL UPDATED SUCCESSFULLY')
    except:
        print('SQL UPDATE ERROR')
        raise LookupError

    cur.close()

    return

def DELETE(table, where):
    '''
    :params (table) the table to delete from
    :params (a_id) the row to delete

    Throws error if table requirements not met
    '''
    # CONNECT TO DATABASE
    conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()

    # PERFORM DELETION AND COMMIT
    sql = f"""DELETE FROM {table} WHERE {where}"""

    print(sql)

    try:
        cur.execute(sql)
        conn.commit()
        print('SQL DELETED SUCCESSFULLY')
    except:
        print('SQL DELETE ERROR')
        raise LookupError

    cur.close()
    conn.close()

    return

def SELECT(table, where, conn=None):
    '''
    :param table: the table to search
    :param a_id: the row to fetch
    :param conn: psycopg2 connection object

    :returns a dict form of the queried row
    Throws error if table requirements not met
    '''

    supplied_conn = True
    # CONNECT TO DATABASE
    if conn == None:
        supplied_conn = False
        conn = psy.connect(os.environ['DATABASE_URL'], sslmode='prefer')
    cur = conn.cursor()

    # QUERY DATABASE
    sql = f"""SELECT * FROM {table} WHERE {where}"""

    print(sql)

    try:
        cur.execute(sql)
        print('SQL SELECTED SUCCESSFULLY')
    except:
        print('SQL SELECT ERROR')
        cur.close()
        conn.close()
        raise LookupError
        return

    rows = cur.fetchall()
    cur.close()
    if not supplied_conn:
        conn.close()

    if rows == None:
        return None

    # FORMAT RESULT
    result = []
    for r in rows:
        if table == 'athletes':
            res = {
                'a_id': r[0],
                'access_token': r[1],
                'refresh_token': r[2],
                'expires_at': r[3],
                'unit': r[4],
                'strava_created': r[5],
                'pr_time': r[6],
                'pr_dist': r[7],
                'username': r[8],
                'profile_pic': r[9],
                'tier': r[10],
                'imported': r[11],
                'customer': r[12],
                'subscription': r[13]}
        elif table == 'activities':
            res = {
                'activity_id': r[0],
                'a_id': r[1],
                'name': r[2],
                'date': r[3],
                'datetime': r[4],
                'dist': r[5],
                'time': r[6],
                'elev': r[7],
                'avg_hr': r[8],
                'intensity': r[9],
                'achievement_count': r[10],
                'kudos_count': r[11],
                'start_lat': r[12],
                'start_lng': r[13],
                'shareable_key': r[14]}
        elif table == 'polylines':
            res = {
                'a_id': r[0],
                'polyline': r[1]
                    }

        result.append(res)

    if len(result) == 1:
        return result[0]

    return result