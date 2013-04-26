//
//  Requires:
//      jquery
//

function leaderboard(callback, limit) {
    limit = limit || 10;
    jQuery.getJSON('/api/leaderboard/' + limit + '?' + Math.random(), function(data) {
        var items = [];
        
        jQuery.each(data.scores, function(key, val) {
            items.push({user:val[0], score:val[1]});
        });

        callback(items);
    });
}

var recordMatchUrlTemplate = new Template("/api/record_match/#{playera.name}:#{playerb.name}/#{playera.score}:#{playerb.score}?");
function recordMatch(playera, playerb, callback) {
    var limit = limit || 10;
    var url = recordMatchUrlTemplate.evaluate({playera:playera, playerb:playerb}) + Math.random();
    jQuery.getJSON(url, function(data) {
        callback(data);
    });
}

var predictMatchUrlTemplate = new Template("/api/predict_match/#{playera.name}:#{playerb.name}?");
function predictMatch(playera, playerb, callback) {
    var url = predictMatchUrlTemplate.evaluate({playera:playera, playerb:playerb}) + Math.random();
    jQuery.getJSON(url, function(data) {
        callback(data);
    });
}

function getAllUsers(callback, limit) {
    limit = limit || 0;
    jQuery.getJSON("/api/all_users/" + limit, function(data) {
        callback(data);
    });
}

function resolvePlayer(player_data, callback) {
    jQuery.getJSON("/api/resolve_player/" + player_data.user, function(data) {
        callback({user:player_data.user, score:player_data.score, name:data.name});
    });
}
