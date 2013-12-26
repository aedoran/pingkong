# Pingkong

This little application maintains a leaderboard of ping pong players based on the results of their individual matches.

![facemash](http://www.leighh.com/wp-content/uploads/2010/11/1286316260-The-Social-Network-window-algorithm.gif)

## Setup

1. Add this repo as a heroku app
2. Setup Google Auth Proxy - follow directions from [this fork](https://github.com/ploxiln/google_auth_proxy/tree/heroku) and set appropriate heroku vars
    * GAPROXY_SECRET
    * GAPROXY_URL
3. Enable mongolab add-on
4. Run `scripts/setup\_production\_db.py` with desired admin user id and name
5. Set ORGNAME config variable if desired
