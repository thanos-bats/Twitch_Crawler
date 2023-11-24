import os
import json
from socketio.client import Client
from dotenv import load_dotenv

load_dotenv()
socket = Client()

@socket.on('connect')
def handle_connect():
    print('Connection established')

@socket.on('disconnect')
def handle_disconnect():
    print('You disconnect from the server')

@socket.on('message')
def handle_message(data):
    print(data)
    streamer_name = data.get('streamer', 'unknown_streamer')

    file_path = get_file_path(streamer_name)
    streamer_messages = load_existing_messages(file_path)
    streamer_messages.append(data)

    save_messages_to_file(file_path, streamer_messages)

def load_existing_messages(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    else:
        return []

def get_file_path(streamer_name):
    parent_folder = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    messages_folder = os.path.join(parent_folder, 'data', 'messages')
    os.makedirs(messages_folder, exist_ok=True)

    return os.path.join(messages_folder, f'{streamer_name}_messages.json')

def start_client():
    try:
        socket.connect(os.getenv('SOCKET_URL'))
        socket.wait()
    except Exception as e:
        print('> Error connecting: ', e)

def save_messages_to_file(file_path, streamer_messages):
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(streamer_messages, json_file, indent=4, ensure_ascii=False)

if __name__ == '__main__': 
    start_client()
