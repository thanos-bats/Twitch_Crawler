# routes/games.py
from flask import jsonify, request
from services.games import search_games_by_keyword, get_game_search
from routes import games_bp
from utilities.utils import get_error_message

@games_bp.route('/', methods=['GET'])
def search_games():
    keyword = request.args.get('keyword')
    number = int(request.args.get('number_of_results', 20))

    if not keyword:
        return get_error_message('keyword')

    return jsonify(search_games_by_keyword(keyword, min(number, 100)))

@games_bp.route('/search', methods=['GET'])
def search_game():
    game_id = request.args.get('game_id')

    if not game_id:
        return get_error_message('game_id')
    
    data = get_game_search(game_id)
    return data
