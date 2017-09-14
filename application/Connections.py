from __future__ import print_function

import psycopg2
import pymongo
from contextlib import contextmanager
from psycopg2.pool import ThreadedConnectionPool
import urllib.request
import re

from application.utils.Singleton import Singleton

@Singleton
class Connection:
    def __init__(self):
        try:
            hosts = ['138.68.92.181']

            with urllib.request.urlopen('http://ipinfo.io/ip') as response:
                html = response.read()
                
            a = re.findall("\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}", str(html))

            h = a[0]

            if h in hosts:
                host = h
            else:
                print("Please select a host: ")
                for i in range(0, len(hosts)):
                    print(str(i+1) + "->" + hosts[i])

                host = hosts[int(input())-1]

            self.MongoDBClient = pymongo.MongoClient('mongodb://admin:smio1EUp@'+host+':27017/', connect=False)
            self.db = self.MongoDBClient.openMakerdB
            self.newsdB = self.MongoDBClient.newsdB
            self.feedDB = self.MongoDBClient.feedDB
            self.conversations = self.MongoDBClient.conversations
            self.events = self.MongoDBClient.events
            self.hashtags = self.MongoDBClient.hashtags
            self.redditFacebookDB = self.MongoDBClient.redditFacebookDB
            self.newsPoolDB = self.MongoDBClient.newsPool
            self.filteredNewsPoolDB = self.MongoDBClient.filteredNewsPool
            self.infDB = self.MongoDBClient.influenceRanks
            self.PostGreSQLConnect = psycopg2.connect(
                "dbname='openmakerdb' user='openmakerpsql' host="+host+" password='smio1EUp'")
            self.cur = self.PostGreSQLConnect.cursor()

            self.pg_pool = psycopg2.pool.ThreadedConnectionPool(
                1, 15,
                host=host,
                port='5432',
                user='openmakerpsql',
                password='smio1EUp',
                database='openmakerdb')

            print("new connection")
        except Exception as e:
            print(e)
            print("I am unable to connect to the database")

    @contextmanager
    def get_cursor(self):
        conn = self.pg_pool.getconn()
        try:
            yield conn.cursor()
            conn.commit()
        finally:
            self.pg_pool.putconn(conn)
