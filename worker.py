# -*- coding: utf-8 -*-
"""
Created on Wed Jun 17 18:14:51 2020

@author: sferg
"""

import os

import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDISTOGO_URL', 'redis://www.run-crunch.com')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()