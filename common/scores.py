# from gevent import monkey; monkey.patch_all()
from pymongo import  DESCENDING
import os
import numpy as np
import pandas as pd
from operator import itemgetter as ig

from mongo import db

# Elo Params
K = int(os.environ.get('ELO_K', 32))
ELO_DEF = int(os.environ.get('ELO_DEF', 1000))

def get_recent_scorings(player, since):
    col = db.scorings
    # a secondary index on ts guarantees that this will get us the most recent score
    res = list(col.find(
        {
        'player': player,
        'ts': {'$gt': since}
        }, 
    ))
    return res

def get_most_recent_score(player, before=None):

    col = db.scorings
    # a secondary index on ts guarantees that this will get us the most recent score
    query = {'player': player}
    if before:
        query['ts'] = {'$lt':before}
    res = col.find_one(query)
    return res['score'] if res else ELO_DEF 

def get_score_timeline(player, since, smooth=True):
    '''
    This will return a pandas timeseries of scores from `since` until the present.
    Pray
    '''
    initial_score = get_most_recent_score(player, before=since)
    recent_scorings = list(reversed(get_recent_scorings(player, since)))
    scores = [initial_score] + map(ig('score'), recent_scorings)
    timestamps = [since] + map(ig('ts'), recent_scorings)
    time_index = pd.DatetimeIndex(np.array(timestamps, dtype='M8[s]'))
    series = pd.TimeSeries(scores, time_index)
    resampled = series.resample('1h')
    interp = resampled.interpolate('time')
    smoothed = pd.ewma(interp, span=24)
    return smoothed if smooth else interp


def update_scores(player_a, score_a, player_b, score_b, match_ts, match_id, _db=db):
    # http://en.wikipedia.org/wiki/Elo_rating_system#Mathematical_details

    # TODO - could parallelize this lookup with gevent...
    R_a = float(get_most_recent_score(player_a))
    R_b = float(get_most_recent_score(player_b))

    S_a = score_a / float(score_a + score_b)
    S_b = score_b / float(score_a + score_b)

    E_a, E_b = compute_expected_scores(R_a, R_b)

    new_R_a = R_a + K * (S_a - E_a)
    new_R_b = R_b + K * (S_b - E_b)

    col = _db.scorings
    def mk_scorings_doc((player, score)):
        return {
            'player': player,
            'score': score,
            'match_id': match_id,
            'ts': match_ts
        }
    map(col.insert, map(mk_scorings_doc, ((player_a, new_R_a), (player_b, new_R_b))))

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

def get_all_players(limit=0, scored_since=0):
    return db.scorings.find(
        {'ts': {'$gt': scored_since}},
        sort=[('score', DESCENDING)], 
        limit=limit
    ).distinct('player')


