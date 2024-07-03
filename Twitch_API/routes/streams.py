# routes/streams.py
from flask import jsonify, request

from services.streams import get_streams, retrieve_comments_start, retrieve_comments_stop, create_jobs_per_streamer, get_all_tags, get_streams_by_tags, evaluate_expression, create_task_background
from routes import streams_bp
from utilities.utils import get_error_message, parse_query

# Returns a list of live streams for a specific game id or a user id
@streams_bp.route('/', methods=['GET'])
def get_game_streams():
    # game_id = request.args.get('game_id')
    #game_ids = request.args.getlist('game_id')
    game_ids_param = request.args.get('game_id')
    game_ids = [int(game_id) for game_id in game_ids_param.split(',')] if game_ids_param else []
    number_of_results = int(request.args.get('number_of_results', 50))
    user_id = request.args.get('user_id', None)
    user_login = request.args.get('user_login', None)
    language = request.args.get('language', None)
    cursor = request.args.get('cursor', None)

    if not game_ids and not user_id and not language and not user_login:
        return get_error_message('game_id, user_id, user_login or language')

    data, status_code = get_streams(game_ids, number_of_results, user_id, user_login, language, cursor, request.path)
    return jsonify(data), status_code

# Starts retrieving comments for a list of live streams
@streams_bp.route('/comments/start', methods=['POST'])
def start_comments_handler():
    data = request.get_json()

    if not data.get('caseId') and not data.get('taskId') and not data.get('streamers'):
        return get_error_message('caseId, taskId and streamers list')
    
    streamers_data, status_code = create_jobs_per_streamer(data.get("streamers"), data.get("taskId"))
    if len(streamers_data["streamers"]) == 0:
        return get_error_message("No Job created into the DB")
    response_data, status_code = retrieve_comments_start(data.get('caseId'), data.get('taskId'), streamers_data.get('streamers'))
    return jsonify(response_data), status_code

# Stops retrieving comments for a crawling id
@streams_bp.route('/comments/stop', methods=['POST'])
def stop_comments_handler():
    data = request.get_json()
    if not data.get('taskId'):
        return get_error_message('taskId')
    
    response_data, status_code = retrieve_comments_stop(data.get('taskId'))
    return jsonify(response_data), status_code

@streams_bp.route('/tags', methods=['GET'])
def get_all_tags_route():
    game_ids_param = request.args.get('game_id')
    game_ids = [int(game_id) for game_id in game_ids_param.split(',')] if game_ids_param else []
    number_of_results = int(request.args.get('number_of_results', 150))
    user_id = request.args.get('user_id', None)
    user_login = request.args.get('user_login', None)
    language = request.args.get('language', None)
    languages = [str(lang) for lang in language.split(',')] if language else []
    crawl_id = request.args.get('crawl_id', None)

    if not game_ids and not user_id and not language and not user_login:
        return get_error_message('game_id, user_id, user_login or language')
    
    data, status_code = get_all_tags(crawl_id, game_ids, user_id, user_login, languages, "/streams/")
    return jsonify(data), status_code

@streams_bp.route('/tags/search', methods=['GET'])
def get_streams_by_tags_route():
    tags_param = request.args.get('tags', None)
    tokens = parse_query(tags_param)
    print(f"Tokens: {tokens}")

    crawl_id = request.args.get('crawl_id')
    game_ids_param = request.args.get('game_ids')
    if (not tags_param) or (not crawl_id):
        return get_error_message("tags and the crawl_id")
    
    game_ids = [int(game_id) for game_id in game_ids_param.split(',')] if game_ids_param else []
    resp = []
    for game_id in game_ids:
        
        tokens_copy = tokens[:]
        print(f"\n\nGAME ID: {game_id}\n-----------------------\nTokens: {tokens_copy}")
        data, status_code = evaluate_expression(tokens_copy, crawl_id, game_id)
        if status_code != 200: return data, status_code
        resp.extend(data)

    print(f"The total length is {len(resp)}")
    return jsonify({"data": resp}), status_code

@streams_bp.route('/comments/background', methods=['POST'])
def create_task_background_route():
    data = request.get_json()
    game_ids_str = data.get('game_id')
    game_ids = [int(game_id) for game_id in game_ids_str.split(',')] if game_ids_str else []

    languages_str = data.get('language', None)
    languages = [str(lang) for lang in languages_str.split(',')] if languages_str else []

    tags_str = data.get('tags', None)
    tags = [str(tag) for tag in tags_str.split(',')] if tags_str else []

    period = data.get('period', 6)
    
    # Here I want to call the create_task_background every 'period' hours
    # Is an API so I want to run at background and continue the code

    resp = "OK"
    status_code = 200
    return jsonify({"data": resp}), status_code