"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

from flask import Flask, render_template, request, redirect
import common.matches
import common.scores
import common.users
import common.util

from operator import itemgetter
from functools import wraps
import os
import json
import time
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')
app.config['GAPROXY_SECRET'] = os.environ.get('GAPROXY_SECRET', 'ruh roh')


def authenticated():
    '''
    Tests whether we are currently authenticated with GAProxy.

    Or just returns true if in debug mode
    '''
    return app.debug or request.headers.get('X-Secret') == app.config['GAPROXY_SECRET']

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not authenticated():
            # gtfo
            return redirect(os.environ.get('GAPROXY_URL'))
        else:
            logging.warn("Authenticated! %s" % getattr(request.authorization, 'username', ''))
            return f(*args, **kwargs)
    return decorated

###
# Routing for your application.
###

@app.route('/')
@requires_auth
def index():
    """Render website's home page."""
    return render_template('index.html')

@app.route('/player/<player_id>')
def player_page(player_id):
    # print 'making api call'
    # url = url_for('api_resolve_player', player_id=player_id, _external=True)
    # print url
    # player_info_task = spawn(lambda: json.loads(urllib2.urlopen(url).read()))
    # # recent_scorings = json.loads()
    # player_info_task.join()
    # try:
    #     player_info = player_info_task.get()
    # except Exception, e:
    #     logging.exception(e)
    #     raise
    # return json.dumps(player_info)
    return render_template('player.html', player_id=player_id)

@app.route('/api/record_match/<player_a>:<player_b>/<int:score_a>:<int:score_b>')
@requires_auth
def api_record_match(player_a, score_a, player_b, score_b):
    diff = abs(score_a - score_b)
    if diff > 21:
        return 'PREPOSTEROUS', 400
    ts = int(time.time())
    reporter = getattr(request.authorization, 'username', '')
    try:
        match_id = common.matches.record_match(
            player_a, score_a, player_b, score_b, ts, reporter)
    except common.matches.Cheating:
        return "CHEATING", 400
    common.scores.update_scores(player_a, score_a, player_b, score_b, ts, match_id)
    return json.dumps("OK")

# @app.route('/api/leaderboard/', defaults={'limit' : 10})
@app.route('/api/leaderboard/<int:limit>')
@requires_auth
def api_leaderboard(limit):
    score_window = 1814400 # seconds in three weeks
    scored_since = int(time.time() - score_window)
    players = common.scores.get_all_players(scored_since=scored_since)
    recent_scores = map(common.scores.get_most_recent_score, players)
    sorted_pairs = sorted(zip(players, recent_scores), key=itemgetter(1), reverse=True)
    return json.dumps({'scores': sorted_pairs})

@app.route('/api/predict_match/<player_a>:<player_b>')
@requires_auth
def api_predict(player_a, player_b):
    data = common.scores.get_expected_result(player_a, player_b)
    return json.dumps({'scores': dict(zip((player_a, player_b), data))})

# @app.route('/api/all_users/', defaults={'limit' : 0})
@app.route('/api/all_users/<int:limit>')
@requires_auth
def api_all_users(limit):
    return json.dumps(common.users.get_all_users(limit, app.debug))

@app.route('/api/resolve_player/<player_id>')
@requires_auth
def api_resolve_player(player_id):
    print 'handling api call'
    found = common.users.get_user(player_id, app.debug)
    if found:
        return json.dumps(found)
    else:
        return '{}', 404

@app.route('/api/recent_scorings/<player_id>/<int:limit>')
@requires_auth
def api_recent_scorings(player_id, limit):
    from_mongo = common.scores.get_most_recent_scorings(player_id, limit)
    converted = [common.util.stringify_bson(m) for m in from_mongo]
    keys_to_return = ['score', 'ts', 'match_id']
    display = [dict((k,v) for k,v in m.iteritems() if k in keys_to_return) for m in converted]
    return json.dumps(sorted(display, key=itemgetter('ts')))

@app.route('/api/recent_matches/<player_id>/<int:limit>')
@requires_auth
def api_recent_matches(player_id, limit):
    def transform_record(rec):
        new_rec = {'ts': rec['ts']}
        if rec['winner'] == player_id:
            new_rec.update({'score': rec['winner_score'], 'opponent': rec['loser'], 'opp_score' : rec['loser_score'], 'outcome' : 'win'})
        else:
            new_rec.update({'score': rec['loser_score'], 'opponent': rec['winner'], 'opp_score' : rec['winner_score'], 'outcome' : 'loss'})
        return new_rec
    records = common.matches.recent_matches(player_id, limit)
    new_records = map(transform_record, records)
    return json.dumps(new_records)




@requires_auth
def api_create_user(player_id, name):
    if not common.users.get_user(request.authorization.username).get('is_admin', False):
        return 'NO', 403
    common.users.create_user(player_id, name)

###
# The functions below should be applicable to all Flask apps.
###

@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=600'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
