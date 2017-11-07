from bson import ObjectId
import datetime
import dateutil.relativedelta
from application.Connections import Connection

prev_month_datetime = datetime.datetime.now() + dateutil.relativedelta.relativedelta(months=-1)
prev_month_objectid = ObjectId.from_datetime(prev_month_datetime)

print(prev_month_objectid)

for topic_id in Connection.Instance().newsPoolDB.collection_names():
    if topic_id != "counters":
        Connection.Instance().db[str(topic_id)].remove({'_id': {'$lte': prev_month_objectid}})
        Connection.Instance().db.command("compact", str(topic_id))
