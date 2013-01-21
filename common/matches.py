from pymongo import MongoClient
import operator

connection = MongoClient(
    # db details here...
    )

def record_match(player_a, score_a, player_b, score_b, match_ts):
    (winner, winner_score), (loser, loser_score) = sorted(
        (
            (player_a, score_a),
            (player_b, score_b),
        ), key=operator.itemgetter(1)
    )
    match = {
        'winner': winner,
        'loser': loser,
        'winner_score': winner_score,
        'loser_score': loser_score,
        'ts': match_ts
    }
    oid = connection.pingkong.matches.insert(match)
    return oid
