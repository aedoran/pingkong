import operator

from mongo import db

def record_match(player_a, score_a, player_b, score_b, match_ts):
    (winner, winner_score), (loser, loser_score) = sorted(
        (
            (player_a, score_a),
            (player_b, score_b),
        ), key=operator.itemgetter(1), reverse=True
    )
    match = {
        'winner': winner,
        'loser': loser,
        'winner_score': winner_score,
        'loser_score': loser_score,
        'ts': match_ts
    }
    oid = db.matches.insert(match)
    return oid
