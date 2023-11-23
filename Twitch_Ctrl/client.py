import os
import json
from socketio.client import Client
from dotenv import load_dotenv

load_dotenv()

socket = Client()
messages = {}

@socket.on('connect')
def handle_connect():
    print('Connection established')

@socket.on('disconnect')
def handle_disconnect():
    print('You disconnect from the server')
    print('The total received messages are:', len(messages))

@socket.on('message')
def handle_message(data):
    print(data)
    streamer_name = data.get('streamer', 'unknown_streamer')

    if streamer_name not in messages:
        messages[streamer_name] = []

    messages[streamer_name].append(data)
    
    # Save messages to a JSON file
    save_messages_to_file(streamer_name)

def start_client():
    try:
        socket.connect(os.getenv('SOCKET_URL'))
        socket.wait()
    except Exception as e:
        print('> Error connecting: ', e)

def save_messages_to_file(streamer_name):
    parent_folder = os.path.abspath(os.path.join(os.getcwd(), os.pardir))  # Get the parent folder

    messages_folder = os.path.join(parent_folder, 'data', 'messages')
    os.makedirs(messages_folder, exist_ok=True)

    file_path = os.path.join(messages_folder, f'{streamer_name}_messages.json')
    
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(messages[streamer_name], json_file, indent=4, ensure_ascii=False)

if __name__ == '__main__': 
    start_client()
