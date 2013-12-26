import os

from pymongo import MongoClient

def get_db(mongo_uri):
    dbname = mongo_uri.rsplit('/',1)[1]
    return getattr(MongoClient(mongo_uri), dbname)

db = get_db(os.environ['MONGOLAB_URI']) if 'MONGOLAB_URI' in os.environ else None
