import threading
from datetime import timezone
import datetime
from app import socketio

def send_command(irc, command):
    print(f'< {command}')
    irc.send((command + '\r\n').encode())

def handle_messages(irc):
    stop_flag = getattr(threading.current_thread(), "stop_flag", False)
    #data = irc.recv(2048).decode()
    
    while not stop_flag:
        try:
            data = irc.recv(2048).decode()
        except Exception as e:
            break

        if not data:
            continue
        elif "PING" in data:
            print("PING - PONG")
            send_command(irc, "PONG tmi.twitch.tv")
        elif "JOIN" in data:
            print("JOIN - successfully joined")
            print(f'> {data}')
        elif "PRIVMSG" in data:
            socketio.emit('message', modify_message(data))
        else:
            print("SOMETHINGELSE: "+data)
        
        stop_flag = getattr(threading.current_thread(), "stop_flag", False)

def modify_message(data):
    data = data.split(':')
    message = data[2].strip()

    data = data[1].split('#')
    channel = data[1]
    username = data[0].split('!')[0]

    data = {
        "streamer":channel, 
        "username": username,
        "message": message,
        "created_at": datetime.datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") 
    }

    return data