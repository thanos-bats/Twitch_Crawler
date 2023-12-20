import os
import json
from socketio.client import Client
from dotenv import load_dotenv
import requests


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
    # data's structure { "data": {Message info}, "channels": {"streamer name": "jobId"} }
    modified_message = data.get('data')
    channels = data.get('channels')
    streamer_name = modified_message.get('streamer', 'unknown_streamer')

    document_data = {
        "jobId": channels.get(streamer_name),
        "domainId": f"twitch:comment:{channels.get(streamer_name)}",
        "title": modified_message.get("message"),
        "content": modified_message.get("message"),
        "raw": "{}",
        "source": "twitch",
        "type": "twitch:comment",
        "publishedAt": modified_message.get("created_at"),
        "discoveredAt": modified_message.get("created_at"),
        "lang": ""
    }
    entity_data = {
        "domainId":f"twitch:profile:{channels.get(streamer_name)}",
        "title":modified_message.get("username"),
        "name":modified_message.get("username"),
        "source":"twitch",
        "type":"twitch:profile",
        "discoveredAt": modified_message.get("created_at")
    }
    print(document_data)
    try:
        create_document_response = requests.post(f"{os.getenv('NEO4J_URL')}/documents/SocialMedia", json=document_data)
        create_entity_response = requests.post(f"{os.getenv('NEO4J_URL')}/entities", json=entity_data)
        
        create_document_response.raise_for_status()
        create_entity_response.raise_for_status()

        print("POST requests successful")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        print("Response Content:", e.response.content)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def load_existing_messages(file_path):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                return json.load(json_file)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            return None
    else:
        print(f"File not found: {file_path}")
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
