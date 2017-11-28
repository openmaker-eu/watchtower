# Author: Kemal Berk Kocabagli

import json
import re
import logic
import time
from application.Connections import Connection
import location_regex # to get regular expressions for locations

def getLocalInfluencers(topic_id, location, cursor):
    cursor = int(cursor)
    result = {}
    try:
        topic_id = int(topic_id)
    except:
        result['local_influencers'] = "topic not found"
        return json.dumps(result, indent=4)
    if (str(topic_id) != "None"):
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_name "
                "FROM topics "
                "WHERE topic_id = %s;"
            )
            cur.execute(sql, [topic_id])
            var = cur.fetchall()
            topic_name = var[0][0]

            # error handling needed for location
            location = location.lower()

            local_influencers = list(
            Connection.Instance().local_influencers_DB[str(topic_id)+"_"+str(location)].find({},
             {'_id': False,
             'name':1,
             'screen_name':1,
             'description':1,
             'location':1,
             'time-zone':1,
             'lang':1,
             'profile_image_url_https':1
             })[cursor:cursor+10]
            )

            result['topic'] = topic_name
            result['location'] = location
            cursor = int(cursor) + 10
            if cursor >= 20 or len(local_influencers) < 10:
                cursor = 0
            result['next_cursor'] = cursor
            result['local_influencers'] = local_influencers
    else:
        result['local_influencers'] = "topic not found"
    return json.dumps(result, indent=4)

def getAudienceSample(topic_id, location, cursor):
    cursor = int(cursor)
    result = {}
    try:
        topic_id = int(topic_id)
    except:
        result['audience_sample'] = "topic not found"
        return json.dumps(result, indent=4)
    if (str(topic_id) != "None"):
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_name "
                "FROM topics "
                "WHERE topic_id = %s;"
            )
            cur.execute(sql, [topic_id])
            var = cur.fetchall()
            topic_name = var[0][0]

            # error handling needed for location
            print("Location: " + str(location))
            location = location.lower()

            audience_sample = list(
            Connection.Instance().audience_samples_DB[str(location)+"_"+str(topic_id)].find({},
            {'_id': False,
            'name':1,
            'screen_name':1,
            'description':1,
            'location':1,
            'time-zone':1,
            'lang':1,
            'profile_image_url_https':1
            })[cursor:cursor+10]
            )

            result['topic'] = topic_name
            result['location'] = location
            cursor = int(cursor) + 10
            if cursor >= 100 or len(audience_sample) < 10:
                cursor = 0
            result['next_cursor'] = cursor
            result['audience_sample'] = audience_sample

    else:
        result['audience_sample'] = "topic not found"
    return json.dumps(result, indent=4)

def getEvents(topic_id, sortedBy, location, cursor):
    now = time.time()
    cursor = int(cursor)
    result = {}
    events = []
    try:
        topic_id = int(topic_id)
    except:
        result['event'] = "topic not found"
        return json.dumps(result, indent=4)
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_name "
            "FROM topics "
            "WHERE topic_id = %s;"
        )
        cur.execute(sql, [topic_id])
        var = cur.fetchall()
        topic_name = var[0][0]

        match = {'end_time': {'$gte': now}}
        sort = {}

        if location !="":
            match['place']= location_regex.getLocationRegex(location)

        if sortedBy == 'interested':
            sort['interested']=-1
        elif sortedBy == 'date' or sortedBy=='':
            sort['start_time']=1
        else:
            return {'error': "please enter a valid sortedBy value."}

        events = Connection.Instance().events[str(topic_id)].aggregate([
            {'$match': match},
            {'$project': {'_id': 0,
                "updated_time": 1,
                "cover": 1,
                "end_time": 1,
                "description":1,
                "id": 1,
                "name": 1,
                "place": 1,
                "start_time": 1,
                "link": 1,
                "interested": 1,
                "coming":1
            }},
            {'$sort': sort},
            {'$skip': int(cursor)},
            {'$limit': 10}
        ])

        events = list(events)
        cursor = int(cursor) + 10
        if cursor >= 100 or len(events) <10:
            cursor = 0
        result['topic'] = topic_name
        result['next_cursor'] = cursor
        result['events']= events
        return result