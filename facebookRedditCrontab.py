from application.Connections import Connection
import praw
import facebook
from praw.models import MoreComments
import json
import re
import requests
import urllib
from datetime import datetime, timedelta
import time
import operator

def mineFacebookConversations(search_ids, timeFilter="day", pageNumber = "5"):
    my_token = Connection.Instance().redditFacebookDB['tokens'].find_one()["facebook"]["token"]
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")

    if timeFilter == "day":
        d = str(datetime.utcnow() - timedelta(hours = 24))
    elif timeFilter == "week":
        d = str(datetime.utcnow() - timedelta(hours = 168))
    elif timeFilter == "month":
        d = str(datetime.utcnow() - timedelta(hours = 730))
    else:
        raise Exception("Wrong time filter!")

    timeAgo = d[:10]+"T"+d[11:19]
    timeAgo = datetime.strptime(timeAgo, "%Y-%m-%dT%H:%M:%S")

    posts = []
    print("search: ", search_ids)
    for ids in search_ids:
        p = graph.get_object(ids+"?fields=feed{permalink_url,attachments,message,created_time,comments{comments,message,created_time,from,attachment}}", page=True, retry=5)
        print("facebook pages: ", ids)
        if "feed" in p:
            for post in p["feed"]["data"]:
                temp = post["created_time"][:-5]
                postTime = datetime.strptime(temp, "%Y-%m-%dT%H:%M:%S")
                if postTime > timeAgo:
                    if "comments" in post:
                        post["comments"] = post["comments"]["data"]
                        for index in range(len(post["comments"])):
                            post["comments"][index]["indent_number"] = 0
                            post["comments"][index]["comment_text"] = post["comments"][index].pop("message")
                            post["comments"][index]["comment_author"] = post["comments"][index]["from"]["name"]
                            post["comments"][index].pop("from")
                        for comment in post["comments"]:
                            if "comments" in comment:
                                comment["comments"] = comment["comments"]["data"]
                                for subComment in comment["comments"]:
                                    subComment["indent_number"] = 1
                                    subComment["comment_text"] = subComment.pop("message")
                                    subComment["comment_author"] = subComment["from"]["name"]
                                    subComment.pop("from")
                        for index in range(len(post["comments"])):
                            if "comments" in post["comments"][index]:
                                post["comments"][index+1:index+1] = post["comments"][index]["comments"]
                                post["comments"][index].pop("comments")
                        post["numberOfComments"] = len(post["comments"])
                    else:
                        post["numberOfComments"] = 0
                    if "message" in post:
                        post["post_text"] = post.pop("message")
                    post["url"] = ""
                    post["source"] = "facebook"
                    post["title"] = ""
                    posts.append(post)
                else:
                    break
    # Sorting all comments with comment numbers, because I will use them in web page in this order
    #posts = sorted(posts, key=lambda k: k["numberOfComments"], reverse=True)
    return posts

def mineRedditConversation(subreddits, timeFilter):
    keys = Connection.Instance().redditFacebookDB['tokens'].find_one()["reddit"]
    reddit = praw.Reddit(client_id=keys["client_id"],
                         client_secret=keys["client_secret"],
                         user_agent=keys["user_agent"],
                        api_type=keys["api_type"])
    posts = []
    for subreddit in subreddits:
        s = reddit.subreddit(subreddit)
        for submission in s.top(time_filter=timeFilter,limit=None):
            try:
                print("reddit: ", submission)
                if (re.search(r"^https://www.reddit.com",submission.url) or re.search(r"^https://i.redd.it",submission.url)):
                    commentStack, comList = [], []
                    submission.comments.replace_more(limit=0)
                    if submission.comments:
                        temp = reversed(submission.comments)
                        for x in temp:
                            commentStack.append([x,0,"true","true"])
                        while commentStack:
                            comment = commentStack.pop()
                            if comment[0].replies:
                                temp = reversed(comment[0].replies)
                                for x in temp:
                                    commentStack.append([x,comment[1]+1,"true","false"])
                                comment[2] = "false"
                            comList.append(comment)
                    cList = []
                    for c in comList:
                        temp = {"parent":c[0].parent_id[3:],"comment_text":c[0].body,"created_time":c[0].created,"comment_id":c[0].id,"indent_number":c[1],"is_leaf":c[2],"is_root":c[3]}
                        if c[0].author:
                            temp["comment_author"] = c[0].author.name
                        else:
                            temp["comment_author"] = "[deleted]"
                        cList.append(temp)

                    posts.append({"source": "reddit", "created_time":submission.created, "title":submission.title, "post_text":submission.selftext, "comments":cList, "url":submission.url, "numberOfComments":len(cList)})
            except:
                print("one submission passed")
                pass

        return posts

def sourceSelection(topicList):
    my_token = Connection.Instance().redditFacebookDB['tokens'].find_one()["facebook"]["token"]
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")

    allSearches = []
    for topic in topicList:
        events = []
        s = graph.get_object('search?q='+topic+'&type=event&limit=100')
        for search in s['data']:
            events.append({'event_id':search['id'],'event_name':search['name']})
        temp = {
            'events' : events
        }
        allSearches.append(temp)
    return allSearches

def mineEvents(topic_id,search_id_list):
    my_token = Connection.Instance().redditFacebookDB['tokens'].find_one()["facebook"]["token"]
    graph = facebook.GraphAPI(access_token=my_token, version="2.7")

    for ids in search_id_list:
        print(ids)
        # event = graph.get_object(id+'?fields=attending_count,cover,description,end_time,id,interested_count,is_canceled,maybe_count,name,noreply_count,owner,place,start_time,timezone,type,updated_time,declined_count,admins,picture,photos,interested,maybe', page=True, retry=5)
        event = graph.get_object(ids+'?fields=attending_count,updated_time,cover,end_time,id,interested_count,name,place,start_time', page=True, retry=5)
        if 'end_time' in event:
            event['end_time'] = time.mktime(datetime.strptime(event['end_time'][:10], "%Y-%m-%d").timetuple())
        else:
            event['end_time'] = time.mktime(datetime.strptime(event['start_time'][:10], "%Y-%m-%d").timetuple())
        try:
            if 'location' in event['place']:
                event['place'] = event['place']['location']['city'] + ", " + event['place']['location']['country']
            else:
                event['place'] = event['place']['name']
        except:
            event['place'] = ''
        event['link'] = 'https://www.facebook.com/events/' + event['id']
        event['start_time'] = event['start_time'][:10]
        event['interested'] = event.pop('interested_count')
        event['coming'] = event.pop('attending_count')
        if 'cover' in event:
            event['cover'] = event['cover']['source']

        ret = Connection.Instance().events[str(topic_id)].aggregate([
            { '$match' : { 'id' : ids } },
            { '$limit' : 1 }
            ])

        if ret.alive:
            newEventUpdateTime = datetime.strptime(event['updated_time'][:-5], "%Y-%m-%dT%H:%M:%S")
            oldEventUpdateTime = datetime.strptime(event['updated_time'][:-5], "%Y-%m-%dT%H:%M:%S")
            if newEventUpdateTime != oldEventUpdateTime:
                print(newEventUpdateTime)
                print(oldEventUpdateTime)
            if newEventUpdateTime > oldEventUpdateTime:
                Connection.Instance().events[str(topic_id)].remove( { 'id' : ids } )
                Connection.Instance().events[str(topic_id)].insert_one(event)
                print('updated')
            else:
                print('existing')
        else:
            Connection.Instance().events[str(topic_id)].insert_one(event)
            print('added new')


def startEvent(topic_id, topicList):
    sources = sourceSelection(topicList)
    for source in sources:
        ids = []
        for event in source['events']:
            ids.append(event['event_id'])
        mineEvents(topic_id,ids)

if __name__ == '__main__':
    Connection.Instance().cur.execute("Select alertid, pages, subreddits, keywords from alerts;")
    var = Connection.Instance().cur.fetchall()

    dates = ["day", "week", "month"]
    for v in var:
        startEvent(v[0], v[3].split(","))
        for date in dates:
            posts = []
            if v[2] != None and v[2] != "":
                subreddits = v[2].split(",")
                posts.extend(mineRedditConversation(subreddits, date))
            if v[1] != None and v[1] != "":
                pages = v[1].split(",")
                posts.extend(mineFacebookConversations(pages, timeFilter=date))
            if len(posts) != 0:
                posts = sorted(posts, key=lambda k: k["numberOfComments"], reverse=True)
                Connection.Instance().conversations[str(v[0])].remove({"time_filter":date})
                Connection.Instance().conversations[str(v[0])].insert_one({'time_filter': date, 'posts': posts})
