# from gevent import monkey; monkey.patch_all()
from pymongo import MongoClient

# Elo Params
K = 20

connection = MongoClient(
    # db details here...
    )

def get_most_recent_score(player):
    col = connection.pingkong.scorings
    res = col.find_one({'player': player})
    return res['score'] if res else 1600 # obviously adjust this later

def update_scores(player_a, score_a, player_b, score_b, match_id, match_ts):
    # http://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details

    # TODO - could parallelize this lookup with gevent...
    R_a = float(get_most_recent_score(player_a))
    R_b = float(get_most_recent_score(player_b))

    S_a = score_a / float(score_a + score_b)
    S_b = score_b / float(score_a + score_b)

    E_a, E_b = compute_expected_scores(R_a, R_b)

    new_R_a = R_a + K * (S_a - E_a)
    new_R_b = R_b + K * (S_b - E_b)

    col = connection.pingkong.scorings
    def mk_scorings_doc(player, score):
        return {
            'player': player,
            'score': score,
            'match_id': match_id,
            'ts': match_ts
        }
    col.insert(mk_scorings_doc(player_a, new_R_a))
    col.insert(mk_scorings_doc(player_b, new_R_b))

def compute_expected_scores(R_a, R_b):
    Q_a = 10 ** (R_a / 400)
    Q_b = 10 ** (R_b / 400)

    E_a = Q_a / (Q_a + Q_b)
    E_b = Q_b / (Q_a + Q_b)

    return E_a, E_b

def get_expected_result(player_a, player_b):
    R_a = float(get_most_recent_score(player_a))
    R_b = float(get_most_recent_score(player_b))
    expected_score_fracs = compute_expected_scores(R_a, R_b)
    return tuple(map(get_expected_result_from_expected_score_frac, expected_score_fracs))

def get_expected_result_from_expected_score_frac(ex, play_till=21.0):
    if ex < 0.5:
        return play_till * ((1 / (1.0 - ex)) - 1)
    else:
        return play_till

