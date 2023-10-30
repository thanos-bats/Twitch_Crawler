# routes/streams.py
from flask import jsonify, request
from services.streams import get_streams, retrieve_comments_start, retrieve_comments_stop
from routes import streams_bp
from utilities.utils import get_error_message

# Returns a list of live streams for a specific game id or a user id
@streams_bp.route('/', methods=['GET'])
def get_game_streams():
    game_id = request.args.get('game_id')
    number_of_results = int(request.args.get('number_of_results', 50))
    user_id = request.args.get('user_id', None)
    language = request.args.get('language', None)

    if not game_id and not user_id and not language:
        return get_error_message('game_id or user_id or language')

    data, status_code = get_streams(game_id, number_of_results, user_id, language, request.path)
    return jsonify(data), status_code

# Starts retrieving comments for a list of live streams
@streams_bp.route('/comments/start', methods=['POST'])
def start_comments_handler():
    data = request.get_json()

    if not data.get('id') and not data.get('streamers'):
        return get_error_message('id and streamers list')
    
    response_data, status_code = retrieve_comments_start(data.get('id'), data.get('streamers'))
    return jsonify(response_data), status_code

# Stops retrieving comments for a crawling id
@streams_bp.route('/comments/stop', methods=['POST'])
def stop_comments_handler():
    data = request.get_json()

    if not data.get('id'):
        return get_error_message('id')
    
    response_data, status_code = retrieve_comments_stop(data.get('id'))
    return jsonify(response_data), status_code