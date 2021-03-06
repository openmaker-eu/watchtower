
__author__ = ['Enis Simsar']

from threading import Thread
import tweepy
from decouple import config

from requests import get

import numpy as np

from logic.helper import add_facebook_pages_and_subreddits
from logic.users import set_user_topics_limit, set_current_topic

import delete_community
from application.Connections import Connection

# Accessing Twitter API
consumer_key = config("TWITTER_CONSUMER_KEY")  # API key
consumer_secret = config("TWITTER_CONSUMER_SECRET")  # API secret
access_token = config("TWITTER_ACCESS_TOKEN")
access_secret = config("TWITTER_ACCESS_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def get_topic_list(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id FROM user_topic WHERE user_id = %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        own_topic_ids = [i[0] for i in var]

        sql = (
            "SELECT topic_id FROM user_topic_subscribe WHERE user_id = %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        subscribe_topic_ids = [i[0] for i in var]

        sql = (
            "SELECT topic_id FROM user_topic WHERE user_id != %s ;"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchall()

        remaining_topics_topics = []
        for i in var:
            if i[0] not in subscribe_topic_ids:
                remaining_topics_topics.append(i[0])

        sql = (
            "SELECT * "
            "FROM topics;"
        )
        cur.execute(sql)
        var = cur.fetchall()

        topics = []

        for i in var:
            sql = (
                "SELECT user_id FROM user_topic WHERE topic_id = %s ;"
            )
            cur.execute(sql, [i[0]])
            var = cur.fetchone()
            sql = (
                "SELECT username FROM users WHERE user_id = %s ;"
            )
            cur.execute(sql, [var[0]])
            var = cur.fetchone()
            temp_topic = {'alertid': i[0], 'name': i[1], 'description': i[2], 'keywords': i[3].split(","),
                          'lang': i[4].split(","), 'creationTime': i[5], 'updatedTime': i[7], 'status': i[8],
                          'publish': i[9], 'newsUpdatedTime': i[10], 'created_by': var[0]}
            if i[0] in own_topic_ids:
                temp_topic['type'] = 'me'
            elif i[0] in subscribe_topic_ids:
                temp_topic['type'] = 'subscribed'
            elif i[0] in remaining_topics_topics:
                temp_topic['type'] = 'unsubscribed'

            def crawl_image(keyword):
                params = {
                    'key': config('PIXABAY_KEY'),
                    'q': keyword,
                    'image_type': 'photo',
                    'safesearch': 'true'
                }
                url = 'https://pixabay.com/api/'

                resp = get(url, params=params)

                if resp.status_code == 200:
                    image = resp.json()
                    if image['hits']:
                        image = np.random.choice(image['hits'])['largeImageURL']
                    else:
                        image = ''
                else:
                    image = ''

                return image
            if not i[12]:
                image = crawl_image(temp_topic['name'])
                if image == '':
                    image = crawl_image(temp_topic['keywords'][0])
                temp_topic['image'] = image
            else:
                temp_topic['image'] = i[12]
            topics.append(temp_topic)

        topics = sorted(topics, key=lambda k: k['alertid'])
        for topic in topics:
            topic['newsCount'] = Connection.Instance().newsPoolDB[str(topic['alertid'])].find().count()
            topic['audienceCount'] = Connection.Instance().audienceDB[str(topic['alertid'])].find().count()
            topic['eventCount'] = Connection.Instance().events[str(topic['alertid'])].find().count()
            topic['tweetCount'] = Connection.Instance().db[str(topic['alertid'])].find().count()
            try:
                hash_tags = list(Connection.Instance().hashtags[str(topic['alertid'])].find({'name': 'month'},
                                                                                            {'month': 1, 'count': 1,
                                                                                             '_id': 0}))[0]['month']
            except:
                hash_tags = []
                pass
            sql = (
                "SELECT ARRAY_AGG(hashtag) FROM topic_hashtag WHERE topic_id = %s ;"
            )
            cur.execute(sql, [topic['alertid']])
            var = cur.fetchone()
            tags = var[0] if var[0] is not None else []
            hash_tags = [
                {'hashtag': hash_tag['hashtag'], 'count': hash_tag['count'], 'active': hash_tag['hashtag'] not in tags}
                for hash_tag in hash_tags]
            topic['hashtags'] = hash_tags

        topics.sort(key=lambda topic: (topic['publish'], topic['newsCount']), reverse=True)
        return topics


def topic_exist(user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT topic_id "
            "FROM user_topic "
            "WHERE user_id = %s"
        )
        cur.execute(sql, [user_id])
        var = cur.fetchone()
        if var is not None:
            return True
        else:
            return False


def get_topic(topic_id):
    if topic_id is not None:
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT * "
                "FROM topics "
                "WHERE topic_id = %s"
            )
            cur.execute(sql, [topic_id])
            var = cur.fetchone()
            topic = {'alertid': var[0], 'name': var[1], 'description': var[2], 'keywords': var[3],
                     'lang': var[4].split(","), 'status': var[8],
                     'keywordlimit': var[6], 'image': var[12]}
    else:
        topic = {'alertid': "", 'name': "", 'keywords': "", 'lang': "", 'status': False, 'keywordlimit': 20,
                 'description': "", 'image': ''}
    return topic


def get_topic_all_of_them_list(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
        var = cur.fetchone()
        print(var)
        topic = {'alertid': var[0], 'name': var[1], 'keywords': var[3].split(","), 'lang': var[4].split(","),
                 'status': var[8]}
        return topic


def add_topic(topic, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "INSERT INTO topics "
            "(topic_name, topic_description, keywords, languages, keyword_limit) "
            "VALUES (%s, %s, %s, %s, %s)"
        )
        cur.execute(sql,
                    [topic['name'], topic['description'], topic['keywords'], topic['lang'], topic['keywordlimit']])
        sql = (
            "SELECT topic_id, topic_name "
            "FROM topics "
            "ORDER BY topic_id DESC "
            "LIMIT 1"
        )
        cur.execute(sql)
        topic_fetched = cur.fetchone()
        print(topic_fetched)

    if topic['name'] == topic_fetched[1]:
        sql = (
            "INSERT INTO user_topic "
            "(user_id, topic_id) "
            "VALUES (%s, %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_fetched[0])])
        topic = get_topic_all_of_them_list(int(topic_fetched[0]))
        set_user_topics_limit(user_id, 'decrement')
        set_current_topic(user_id)
        t = Thread(target=add_facebook_pages_and_subreddits, args=(topic_fetched[1], topic['keywords'],))
        t.start()


def delete_topic(topic_id, user_id):
    alert = get_topic_all_of_them_list(topic_id)
    set_user_topics_limit(user_id, 'increment')
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT * "
            "FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
        topic = cur.fetchone()
        topic = list(topic)
        topic.append(int(user_id))
        sql = (
            "INSERT INTO public.archived_topics "
            "(topic_id, topic_name, topic_description, keywords, languages, creation_time, "
            "keyword_limit, last_tweet_date, is_running, is_publish, user_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        )
        cur.execute(sql,
                    [topic[0], topic[1], topic[2], topic[3], topic[4], topic[5], topic[6], topic[7], topic[8],
                     topic[9],
                     int(user_id)])
        sql = (
            "DELETE FROM topics "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
        sql = (
            "DELETE FROM user_topic "
            "WHERE topic_id = %s AND user_id = %s"
        )
        cur.execute(sql, [topic_id, user_id])
        sql = (
            "DELETE FROM topic_facebook_page "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
        sql = (
            "DELETE FROM topic_subreddit "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [topic_id])
    set_current_topic(user_id)

    t = Thread(target=delete_community.main, args=(alert['alertid'],))
    t.start()


def update_topic(topic):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET topic_description = %s, keywords = %s, languages = %s, keyword_limit = %s, image = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql,
                    [topic['description'], topic['keywords'], topic['lang'], topic['keywordlimit'], topic['image'],
                     topic['alertid']])
    topic = get_topic_all_of_them_list(topic['alertid'])
    t = Thread(target=add_facebook_pages_and_subreddits, args=(topic['alertid'], topic['keywords'],))
    t.start()


def start_topic(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_running = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [True, topic_id])


def stop_topic(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_running = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [False, topic_id])


def publish_topic(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_publish = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [True, topic_id])


def unpublish_topic(topic_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "UPDATE topics "
            "SET is_publish = %s "
            "WHERE topic_id = %s"
        )
        cur.execute(sql, [False, topic_id])


def subsribe_topic(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_topic_subscribe where user_id = %s and topic_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id)])
        fetched = cur.fetchone()

        if not fetched[0]:
            sql = (
                "INSERT INTO user_topic_subscribe "
                "(user_id, topic_id) "
                "VALUES (%s, %s)"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])


def unsubsribe_topic(topic_id, user_id):
    with Connection.Instance().get_cursor() as cur:
        sql = (
            "SELECT EXISTS (SELECT 1 FROM user_topic_subscribe where user_id = %s and topic_id = %s)"
        )
        cur.execute(sql, [int(user_id), int(topic_id)])
        fetched = cur.fetchone()
        if fetched[0]:
            sql = (
                "DELETE FROM user_topic_subscribe "
                "WHERE user_id = %s and topic_id = %s;"
            )
            cur.execute(sql, [int(user_id), int(topic_id)])
            sql = (
                "UPDATE users "
                "SET current_topic_id = %s "
                "WHERE user_id = %s"
            )
            cur.execute(sql, [None, int(user_id)])
