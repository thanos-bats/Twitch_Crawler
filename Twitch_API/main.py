from app import create_app, socketio
from apscheduler.schedulers.background import BackgroundScheduler
from services.games import get_games
import threading
import datetime

app = create_app()
scheduler = BackgroundScheduler()

def run_scheduler():
     with app.app_context():
        get_games(None, {"data": []})
        scheduler.add_job(func=get_games, args=(None, {"data": []}), trigger='interval', hours=1)
        print('Scheduler started at ', datetime.datetime.now())
        scheduler.start()

def run_app():
    print('> Starting socketio.run(app)')  
    socketio.run(app, port=3000, host="0.0.0.0", use_reloader=False, allow_unsafe_werkzeug=True, debug=True)

if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()

    run_app()