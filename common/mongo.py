import os

from pymongo import MongoClient

mongo_uri = os.environ['MONGOLAB_URI']
dbname = mongo_uri.rsplit('/',1)[1]
db = getattr(MongoClient(mongo_uri), dbname)
