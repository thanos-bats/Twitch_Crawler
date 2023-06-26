from utilities.utils import get_dotenv, get_data, create_dict_from_vars
from utilities.irc_utils import *
import socket
import random
import string
import threading

def get_streams(game_id, number_of_results, user_id, endpoint):
    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"

    
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    params = create_dict_from_vars(game_id=game_id, user_id=user_id)
    print(f'Headers {headers}')
    print(f'params {params}')
    print()
    response_data, response_status = get_data(url, params, headers, number_of_results, None, {"data": []})
    print(f'the response data: {response_data}')
    print(f'the response status: {response_status}')
    for item in response_data["data"]:
        item.pop("type", None)
        item["stream_url"] = "https://www.twitch.tv/" + item.pop("user_login", None)
        item.pop("tags", None)

    return response_data, response_status

irc_connections = {}
irc_threads = {}
def retrieve_comments_start(crawling_id, channels):
    if crawling_id in irc_connections.keys():
        response_data = {
            'id': crawling_id,
            'message': 'The id already exists'
        }
        return response_data, 400
    
    HOST = 'irc.chat.twitch.tv'
    PORT = 6667

    oauth_token = 'oauth:' + ''.join(random.choices(string.ascii_letters + string.digits, k=30))    # 'oauth:u800sfpa0b6nuaqsyg7queipflza5e'
    username = 'justinfan' + str(random.randint(1, 999))

    irc = socket.socket()
    irc.connect((HOST, PORT))
    send_command(irc, f'PASS {oauth_token}')
    send_command(irc, f'NICK {username}')

    for channel in channels:
        send_command(irc, f'JOIN #{channel}')

    resp =  irc.recv(2048).decode()
    if 'failed' in resp:
        response_data = {
            'id': crawling_id,
            'message': resp
        }
        return response_data, 404
    
    irc_thread = threading.Thread(target=handle_messages, args=(irc,))
    irc_thread.start()
    

    irc_threads[crawling_id] = irc_thread
    irc_connections[crawling_id] = irc

    response_data = {
        'id': crawling_id,
        'channels': channels,
        'message': 'Connection started successfully'
    }
    return response_data, 200

def retrieve_comments_stop(crawling_id):
    irc = irc_connections.get(crawling_id)
    irc_thread = irc_threads.get(crawling_id)

    if irc_thread and irc:
        irc_thread.stop_flag = True
        
        irc.close()
        
        del irc_threads[crawling_id]
        del irc_connections[crawling_id]

        response_data = {
            'id': crawling_id,
            'message': 'Connection stoped successfully'
        }
        return response_data, 200
    else:
        response_data = {
            "id": crawling_id,
            'message': 'Connection not found. Please give a correct id'
        }
        return response_data, 404