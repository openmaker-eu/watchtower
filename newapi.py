import pymongo
from application.Connections import Connection

def getThemes(userid):
    Connection.Instance().cur.execute("select alertid, alertname from alerts where userid = %s", [userid])
    var = Connection.Instance().cur.fetchall()
    themes = [{'alertid':i[0], 'name':i[1]} for i in var]
    result = {}
    result['themes'] = themes
    return json.dumps(result, indent=4)

def getFeeds(themename, userid, date, cursor):
    dates=['all', 'yesterday', 'week', 'month']
    result = {}
    if date not in dates:
        result['Error'] = 'invalid date'
        return json.dumps(result, indent=4)
    themeid = str(logic.getAlertIdwithUserId(themename, userid))
    feeds = list(Connection.Instance().db[themeid].find({'name': date}, {date: 1}))
    feeds = list(feeds[0][yesterday][cursor:cursor+20])
    if len(feeds) == 0:
        print len(list(feeds))
        feeds.append("Cursor is Empty.")
    else:
        cursor = int(cursor) + 20
        if cursor >= length:
            cursor = length
        result['next_cursor'] = cursor
    result['cursor_length'] = 100
    result['feeds'] = feeds
    return json.dumps(result, indent=4)
