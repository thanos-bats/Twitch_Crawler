from app import create_app, socketio

app = create_app()

print('> Starting socketio.run(app)')
socketio.run(app, debug=False, port=3000, host="0.0.0.0")