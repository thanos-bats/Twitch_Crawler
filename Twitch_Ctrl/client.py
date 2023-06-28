import os
from socketio.client import Client
from dotenv import load_dotenv

load_dotenv()

socket = Client()
messages = []

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
    messages.append(data)

def start_client():
    try:
        socket.connect(os.getenv('SOCKET_URL'))
    except Exception as e:
        print('> Error connecting: ', e)

    while True:
        message = input('Enter "quit" to exit\n')
        if message.lower() == 'quit':
            break

    socket.disconnect()

if __name__ == '__main__':
    start_client()
