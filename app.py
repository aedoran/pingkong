"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

from flask import Flask, render_template, request
import common.matches
import common.scores
import common.users

from operator import itemgetter
from functools import wraps
import os
import json
import time
import math
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')
app.config['GAPROXY_SECRET'] = os.environ.get('GAPROXY_SECRET', 'ruh roh')

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-Secret') != app.config['GAPROXY_SECRET']:
            # gtfo
            return 'GTFO', 403
        else:
            logging.warn("Authenticated! %s" % request.authorization.username)
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

@app.route('/api/record_match/<player_a>:<player_b>/<int:score_a>:<int:score_b>/')
@requires_auth
def api_record_match(player_a, score_a, player_b, score_b):
    diff = math.abs(score_a - score_b)
    if diff > 21:
        return 'PREPOSTEROUS', 400
    ts = int(time.time())
    match_id = common.matches.record_match(player_a, score_a, player_b, score_b, ts)
    common.scores.update_scores(player_a, score_a, player_b, score_b, ts, match_id)
    return json.dumps("OK")

@app.route('/api/leaderboard', defaults={'limit' : 10})
@app.route('/api/leaderboard/<int:limit>')
@requires_auth
def api_leaderboard(limit):
    players = common.scores.get_all_players()
    recent_scores = map(common.scores.get_most_recent_score, players)
    sorted_pairs = sorted(zip(players, recent_scores), key=itemgetter(1), reverse=True)
    return json.dumps({'scores': sorted_pairs})

@app.route('/api/predict_match/<player_a>:<player_b>')
@requires_auth
def api_predict(player_a, player_b):
    data = common.scores.get_expected_result(player_a, player_b)
    return json.dumps({'scores': dict(zip((player_a, player_b), data))})

@app.route('/api/all_users', defaults={'limit' : 0})
@app.route('/api/all_users/<int:limit>')
@requires_auth
def api_all_users(limit):
    return json.dumps(common.users.get_all_users(limit, app.debug))

@app.route('/api/resolve_player/<player_id>')
@requires_auth
def api_resolve_player(player_id):
    found = common.users.get_user(player_id, app.debug)
    if found:
        return json.dumps(found)
    else:
        return '{}', 404

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
