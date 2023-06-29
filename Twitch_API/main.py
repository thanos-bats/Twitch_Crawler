from app import create_app, socketio
from apscheduler.schedulers.background import BackgroundScheduler
from services.games import get_games
import threading


app = create_app()

scheduler = BackgroundScheduler()

def run_scheduler():
    scheduler.add_job(func=get_games, args=(None, {"data": []}), trigger='interval', hours=1)
    print('Scheduler started')
    scheduler.start()

def run_app():
    print('> Starting socketio.run(app)')
    socketio.run(app, debug=False, port=3000, host="0.0.0.0", allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    run_app()