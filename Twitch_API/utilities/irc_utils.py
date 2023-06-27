import threading
from datetime import timezone
import datetime
from app import socketio
import re

def send_command(irc, command):
    print(f'< {command}')
    irc.send((command + '\r\n').encode())

def handle_messages(irc):
    stop_flag = getattr(threading.current_thread(), "stop_flag", False)
    
    while not stop_flag:
        try:
            data = irc.recv(2048).decode()
        except Exception as e:
            break

        if not data:
            continue

        for msg in data.strip().split("\n"):
            if "PING" in msg:
                print("PING - PONG")
                send_command(irc, "PONG tmi.twitch.tv")
            elif "JOIN" in msg:
                print("JOIN - successfully joined")
                print(f'> {msg}')
            elif "PRIVMSG" in msg:
                try:
                    modified_message = modify_message(msg)
                    socketio.emit('message', modified_message)
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print(">>: "+ msg)
        
        stop_flag = getattr(threading.current_thread(), "stop_flag", False)

def modify_message(data):
    pattern = r":(?P<username>[^!]+)![^#]+#(?P<streamer>[^\s]+)\s*:(?P<message>.*)"
    match = re.match(pattern, data)
    
    if not match:
        return None

    username = match.group('username')
    streamer = match.group('streamer')
    message = match.group('message').strip()

    data = {
        "streamer": streamer, 
        "username": username,
        "message": message,
        "created_at": datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") 
    }

    return data