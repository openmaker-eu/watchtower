from application.Connections import Connection
import sys
import time

influencerDB = Connection.Instance().influencerDB
audienceDB = Connection.Instance().audienceDB
localInfluencersDB = Connection.Instance().local_influencers_DB
audienceSamplesDB = Connection.Instance().audience_samples_DB
audienceNetworksDB = Connection.Instance().audience_networks_DB

def delete_influencers(topic_id):
    influencerDB['all_influencers'].update(
        {'id': {'$in':Connection.Instance().influencerDB[str(topic_id)].distinct('id')}},
        {'$pull':{'topics': int(topic_id)}},
        multi=True
    )
    print("Deleted the topic from topics.")
    result = influencerDB['all_influencers'].delete_many(
        {'$where':'this.topics.length<1'}
    )
    print("Deleted " + str(result.deleted_count) + " influencers from all_influencers.")

def delete_audience(topic_id):
    try:
        audienceDB['all_audience'].update(
            {'id': {'$in':Connection.Instance().audienceDB[str(topic_id)].distinct('id')}},
            {'$pull':{'topics': int(topic_id)}},
            multi=True
        )
    except:
        audienceDB['all_audience'].update({},
            {'$pull':{'topics': int(topic_id)}},
            multi=True
        )
    print("Deleted the topic from topics.")

    try:
        result = audienceDB['all_audience'].delete_many(
            {
            'id': {'$in':Connection.Instance().audienceDB[str(topic_id)].distinct('id')},
            '$where':'this.topics.length<1'
            }
        )
    except:
        result = audienceDB['all_audience'].delete_many(
            {'$where':'this.topics.length<1'}
        )

    print("Deleted " + str(result.deleted_count) + " audience members from all_audience.")

def delete_local_influencers(topic_id):
    cn = localInfluencersDB.collection_names()
    collections_to_drop = [c for c in cn if str(topic_id) in c]

    for collection in collections_to_drop:
        localInfluencersDB.drop[collection]

def delete_audience_samples(topic_id):
    cn = audienceSamplesDB.collection_names()
    collections_to_drop = [c for c in cn if "_" + str(topic_id) in c]

    for collection in collections_to_drop:
        audienceSamplesDB.drop[collection]

def delete_audience_members(topic_id):
    try:
        audienceNetworksDB['all_audience'].update(
            {'id': {'$in':Connection.Instance().audienceDB[str(topic_id)].distinct('id')}},
            {'$pull':{'topics': int(topic_id)}},
            multi=True
        )
    except:
        audienceNetworksDB['all_audience'].update({},
            {'$pull':{'topics': int(topic_id)}},
            multi=True
        )
    print("Deleted the topic from topics.")

    try:
        result = audienceNetworksDB['all_audience'].delete_many(
            {
            'id': {'$in':Connection.Instance().audienceDB[str(topic_id)].distinct('id')},
            '$where':'this.topics.length<1'
            }
        )
    except:
        result = audienceNetworksDB['all_audience'].delete_many(
            {'$where':'this.topics.length<1'}
        )

    print("Deleted " + str(result.deleted_count) + " audience members from all_audience_members.")

def main():
    if (len(sys.argv) == 2):
        with Connection.Instance().get_cursor() as cur:
            sql = (
                "SELECT topic_id, topic_name "
                "FROM archived_topics "
                "WHERE audience_deleted=false "
            )
            cur.execute(sql)
            topics = cur.fetchall()  # list of all topics
            topic_ids=[]
            print('topic ID    topic name')
        for topic in topics:
            topic_ids.append(str(topic[0]))
            print(str(topic[0]) + " " + str(topic[1]))
        topic_to_delete = -1
        while(topic_to_delete not in topic_ids):
            topic_to_delete = str(input('Which topic would you like to delete (enter the ID)? '))

        start = time.time()
        print("Do not forget to inactivate the topic in PostgreSQL DB!!!")

        print("Deleting influencers...")
        delete_influencers(topic_to_delete)
        print("Complete in " + str(time.time()-start) + " seconds.")
        start = time.time()

        print("Deleting audience...")
        delete_audience(topic_to_delete)
        print("Complete in " + str(time.time()-start) + " seconds.")
        start = time.time()

        print("Deleting local influencers...")
        delete_local_influencers(topic_to_delete)
        print("Complete in " + str(time.time()-start) + " seconds.")
        start = time.time()

        print("Deleting audience samples...")
        delete_audience_samples(topic_to_delete)
        print("Complete in " + str(time.time()-start) + " seconds.")
        start = time.time()

        print("Deleting audience members...")
        delete_audience_members(topic_to_delete)
        print("Complete in " + str(time.time()-start) + " seconds.")
        start = time.time()

        with Connection.Instance().get_cursor() as cur:
            sql = (
                "UPDATE archived_topics "
                "SET audience_deleted = %s "
                "WHERE topic_id = %s"
            )
            cur.execute(sql, [True, int(topic_to_delete)])
            print("Updated PostgreSQL DB.")

    else:
        print("Usage: delete_topic.py <server_ip> \n staging: 138.68.92.181\n production: 194.116.76.78")

if __name__ == "__main__":
    main()