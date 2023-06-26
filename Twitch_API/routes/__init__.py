# routes/__init__.py
from flask import Blueprint

# Create blueprints for each route file
games_bp = Blueprint('games', __name__, url_prefix='/games')
streams_bp = Blueprint('streams', __name__, url_prefix='/streams')
videos_bp = Blueprint('videos', __name__, url_prefix='/videos')
users_bp = Blueprint('users', __name__, url_prefix='/users')

# Import route files to register blueprints
from routes.games import *
from routes.streams import *
from routes.videos import *
from routes.users import *