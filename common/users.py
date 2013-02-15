from mongo import db

def get_user(uid, allow_test):
    query = {'_id' : uid}
    if not allow_test:
        query['is_test'] = False
    return db.users.find_one(query)
