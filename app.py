"""
Flask Documentation:     http://flask.pocoo.org/docs/
Jinja2 Documentation:    http://jinja.pocoo.org/2/documentation/
Werkzeug Documentation:  http://werkzeug.pocoo.org/documentation/

This file creates your application.
"""

import os
from flask import Flask, render_template, request, redirect, url_for
import common.matches
import common.scores
from operator import itemgetter
import json

import time

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'this_should_be_configured')


###
# Routing for your application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html')

@app.route('/record_match', methods=['POST'])
def record_match():
    ts = int(time.time())
    args = [request.form[arg] for arg in ['player_a', 'score_a', 'player_b', 'score_b']] \
        + [ts]
    match_id = common.matches.record_match(*args)
    common.scores.update_scores(*(args + [match_id]))

@app.route('/leaderboard')
def leaderboard():
    players = common.scores.get_all_players()
    recent_scores = map(common.scores.get_most_recent_score, players)
    sorted_pairs = sorted(zip(players, recent_scores), key=itemgetter(1), reverse=True)
    return json.dumps({'scores': sorted_pairs})


###
# The functions below should be applicable to all Flask apps.
###

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


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
