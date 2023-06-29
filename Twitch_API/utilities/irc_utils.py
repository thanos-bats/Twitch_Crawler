import threading
from datetime import timezone
import datetime
from app import socketio
import re

def send_command(irc, command):
    print(f'< {command}')
    irc.send((command + '\r\n').encode())

def handle_messages(irc, crawling_id):
    stop_flag = getattr(threading.current_thread(), "stop_flag", False)
    
    while not stop_flag:
        try:
            data = irc.recv(2048).decode()
            if not data:
                continue

            for msg in data.strip().split("\n"):
                if "PING" in msg:
                    send_command(irc, "PONG tmi.twitch.tv")
                elif "JOIN" in msg:
                    print(f'> {msg}')
                elif "PRIVMSG" in msg:
                    modified_message = modify_message(crawling_id, msg)
                    if modified_message:
                        socketio.emit('message', modified_message)
                else:
                    print(">>: "+ msg)
            
            stop_flag = getattr(threading.current_thread(), "stop_flag", False)
        except Exception as e:
            break

        

def modify_message(crawling_id, data):
    pattern = r":(?P<username>[^!]+)![^#]+#(?P<streamer>[^\s]+)\s*:(?P<message>.*)"
    match = re.match(pattern, data)
    
    if not match:
        return None

    username = match.group('username')
    streamer = match.group('streamer')
    message = match.group('message').strip()

    data = {
        "id": crawling_id,
        "streamer": streamer, 
        "username": username,
        "message": message,
        "created_at": datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") 
    }

    return data