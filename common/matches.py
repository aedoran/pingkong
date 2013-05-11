import operator

from mongo import db

class Cheating(Exception):
    pass

def record_match(player_a, score_a, player_b, score_b, match_ts, reporter=None):
    (winner, winner_score), (loser, loser_score) = sorted(
        (
            (player_a, score_a),
            (player_b, score_b),
        ), key=operator.itemgetter(1), reverse=True
    )
    if winner == reporter:
        raise Cheating()
    match = {
        'winner': winner,
        'loser': loser,
        'winner_score': winner_score,
        'loser_score': loser_score,
        'ts': match_ts
    }
    oid = db.matches.insert(match)
    return oid

def recent_matches(player_id, limit):
    col = db.matches
    query = {'$or' : [{'winner': player_id}, {'loser' : player_id}]}
    res = col.find(query, sort=[('ts',-1)], limit=limit)
    return list(res)
