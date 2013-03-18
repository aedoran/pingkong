from collections import defaultdict
import bson

class ArgDefaultDict(defaultdict):
    pass # TODO copy out my gist

def stringify_bson(bson_obj):
    for k,v in bson_obj.iteritems():
        if isinstance(v, bson.objectid.ObjectId):
            bson_obj[k] = str(v)
    return bson_obj
