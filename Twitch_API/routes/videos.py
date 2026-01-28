# routes/videos.py
from flask import jsonify, request
from services.videos import get_videos
from routes import videos_bp
from utilities.utils import get_error_message

# Returns a list of Vods that match the given twitch game id or user id
@videos_bp.route('/', methods=['GET'])
def get_game_videos():
    game_id = request.args.get('game_id')
    number_of_results = int(request.args.get('number_of_results', 50))
    sorting_type = request.args.get('sort', 'time')
    user_id = request.args.get('user_id', None)

    if not game_id and not user_id:
        return get_error_message('game_id or user_id')
        
    data, status_code = get_videos(game_id, number_of_results, user_id, request.path, sorting_type)
    print(f"The video data is {len(data['data'])}\nwith status code {status_code}")

    return jsonify(data), status_code
