"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

from flask import Flask, render_template, request, redirect
from flask.ext.wtf import Form, TextField, DataRequired

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
import vincent

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')
app.config['GAPROXY_SECRET'] = os.environ.get('GAPROXY_SECRET', 'ruh roh')
app.debug = bool(int(os.environ.get('PINGKONGDEV', 0)))

ORGNAME = os.environ.get('ORGNAME', 'Bitly')

SECONDS_IN_3_WEEKS = 1814400 # seconds in three weeks

def _current_user():
    return getattr(request.authorization, 'username', '')

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
            logging.warn("Authenticated! %s" % _current_user())
            return f(*args, **kwargs)
    return decorated

def admin_only(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # lookup user and see if they are admin
        user_info = common.users.get_user(_current_user())
        if not(app.debug or user_info and user_info.get('is_admin', False)):
            return 'GTFO', 403
        return f(*args, **kwargs)
    return decorated

###
# Routing for your application.
###

@app.route('/')
@requires_auth
def index():
    """Render website's home page."""
    return render_template('index.html', org=ORGNAME)

@app.route('/player/<player_id>')
def player_page(player_id):
    return render_template('player.html', player_id=player_id, org=ORGNAME)

@app.route('/api/record_match/<player_a>:<player_b>/<int:score_a>:<int:score_b>')
@requires_auth
def api_record_match(player_a, score_a, player_b, score_b):
    diff = abs(score_a - score_b)
    if diff > 21:
        return 'PREPOSTEROUS', 400
    ts = int(time.time())
    reporter = _current_user()
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
    score_window = SECONDS_IN_3_WEEKS
    scored_since = int(time.time() - score_window)
    players = common.scores.get_all_players(scored_since=scored_since)
    recent_scores = map(common.scores.get_most_recent_score, players)
    sorted_pairs = sorted(zip(players, recent_scores), key=itemgetter(1), reverse=True)
    return json.dumps({'scores': sorted_pairs})

@app.route('/api/predict_match/<player_a>:<player_b>')
@requires_auth
def api_predict(player_a, player_b):
    data = common.scores.get_expected_result(player_a, player_b)
    return json.dumps({'scores': dict(zip((player_a, player_b), data)), 
                       'current_user': _current_user()})

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

@app.route('/api/score_timeline/<player_id>')
@requires_auth
def api_score_timeline(player_id):
    score_series = common.scores.get_score_timeline(player_id, int(time.time()) - SECONDS_IN_3_WEEKS)
    vis = vincent.Area()
    vis.tabular_data(score_series, axis_time='day')
    vis += ({'labels': {'angle': {'value': 25}}}, 'axes', 0, 'properties')
    vis += ({'value': 22}, 'axes', 0, 'properties', 'labels', 'dx')
    vis.update_vis(padding={'bottom': 50, 'left': 60, 'right': 40, 'top': 10})
    vis.update_vis(width=700)

    # here we go..
    # determine the bottom limit - pad below by a bit, and truncate to mult of 10
    domain_min = round((score_series.min() - 10) / 10.0) * 10
    vis += (False, 'scales', 1, 'zero')
    vis += (domain_min, 'scales', 1, 'domainMin')
    vis += (domain_min, 'marks', 0, 'properties', 'enter', 'y2', 'value')

    # colors..
    # remove the hover color change, it is stupid
    vis -= ('hover', 'marks', 0, 'properties')
    # and change the main color to red because I wanna
    vis += ({'value' : '#c1251f'}, 'marks', 0, 'properties', 'update', 'fill')
    return json.dumps(vis.vega)

# Admin stuff

@app.route('/admin', methods=['GET', 'POST'])
@requires_auth
@admin_only
def admin():
    form = CreateUserForm(request.form, csrf_enabled=False)
    if request.method == 'POST' and form.validate():
        common.users.create_user(form.uid.data, form.name.data)
        logging.warn('%s created user %s' % (_current_user(), form.uid.data))
        return redirect('/admin')
    return render_template('admin.html', form=form, org=ORGNAME)

class CreateUserForm(Form):
    name = TextField('name', validators=[DataRequired()])
    uid = TextField('uid', validators=[DataRequired()])

@requires_auth
@admin_only
def api_create_user(player_id, name):
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
    return redirect('http://bukk.it/invalid.jpg')


if __name__ == '__main__':
    app.run(debug=True)
