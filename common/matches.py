from pymongo import MongoClient

connection = MongoClient(
    # db details here...
    )

def record_match(player_a, score_a, player_b, score_b, match_ts):
    winner = player_a if score_a > score_b else player_b
    loser = (set([player_a, player_b]) - set([winner])).pop()
    match = {
        'winner': winner,
        'loser': loser,
        'winner_score': max(score_a, score_b),
        'loser_score': min(score_a, score_b),
        'ts': match_ts
    }
    oid = connection.pingkong.matches.insert(match)
    return oid
