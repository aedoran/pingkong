"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

from flask import Flask, render_template
import common.matches
import common.scores

from operator import itemgetter
import os
import json
import time


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')

###
# Routing for your application.
###

@app.route('/')
def index():
    """Render website's home page."""
    return render_template('index.html')

@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html')

@app.route('/api/record_match/<player_a>:<player_b>/<int:score_a>:<int:score_b>/')
def record_match(player_a, score_a, player_b, score_b):
    ts = int(time.time())
    match_id = common.matches.record_match(player_a, score_a, player_b, score_b, ts)
    common.scores.update_scores(player_a, score_a, player_b, score_b, ts, match_id)
    return json.dumps("OK")

@app.route('/api/leaderboard', defaults={'limit' : 10})
@app.route('/api/leaderboard/<int:limit>')
def leaderboard(limit):
    players = common.scores.get_all_players()
    recent_scores = map(common.scores.get_most_recent_score, players)
    sorted_pairs = sorted(zip(players, recent_scores), key=itemgetter(1), reverse=True)
    return json.dumps({'scores': sorted_pairs})

@app.route('/api/predict/<player_a>:<player_b>')
def predict(player_a, player_b):
    data = common.scores.get_expected_result(player_a, player_b)
    return json.dumps({'scores': dict(zip((player_a, player_b), data))})


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
