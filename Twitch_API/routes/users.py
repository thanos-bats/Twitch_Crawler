#routes/users.py
from routes import users_bp
from flask import jsonify, request
from utilities.utils import get_error_message
from services.users import get_user

@users_bp.route('/', methods=['GET'])
def search_user():
    user_name = request.args.get('user_name')
    user_id = request.args.get('user_id')

    if not user_name and not user_id:
        return get_error_message('user_name or user_id')
    
    data, status_code = get_user(user_name, user_id, request.path)
    return jsonify(data), status_code
