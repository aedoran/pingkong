from mongo import db

def get_user(uid, allow_test=False):
    query = {'_id' : uid}
    if not allow_test:
        query['is_test'] = False
    return db.users.find_one(query)

def get_all_users(limit=0, allow_test=False):
    query = {}
    if not allow_test:
        query['is_test'] = False
    return list({"name":i["name"], "id":i["_id"]} for i in db.users.find(query, limit=limit))

def create_user(uid, name):
    doc = {
        '_id' : uid,
        'name' : name
    }
    db.users.insert(doc)
