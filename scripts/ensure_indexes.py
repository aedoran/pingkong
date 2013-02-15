import pymongo

def ensure_collection_indexes(db):
    matches = db.matches
    # { _id, winner: df, loser: josh, ts: 1234, ...}
    matches.ensure_index('winner', pymongo.ASCENDING)
    matches.ensure_index('loser', pymongo.ASCENDING)
    matches.ensure_index('ts', pymongo.DESCENDING)

    scorings = db.scorings
    # { _id, player: df, ts: 1234, score: 1234}

    # so the thinking here was to do a compound index...
    scorings.ensure_index([('player', pymongo.ASCENDING), ('ts', pymongo.DESCENDING)])
    # though I'm still not sure how well that query will work

    # new idea is just to have single indexes for both player and ts
    # then to look up each player's most recent score, we do a distinct and then a bunch of findOnes
    # still actually need that compound also! right?
    scorings.ensure_index('ts', pymongo.DESCENDING)



def add_test_users(db, user_tups):
    col = db.users
    for name, uid, is_test in user_tups:
        doc = {
            '_id' : uid,
            'name' : name,
            'is_test' : is_test
        }
        col.insert(doc)
