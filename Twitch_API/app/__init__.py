from flask import Flask

from .events import socketio
from routes import games_bp, streams_bp, videos_bp, users_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(games_bp)
    app.register_blueprint(streams_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(users_bp)

    socketio.init_app(app)

    return app
