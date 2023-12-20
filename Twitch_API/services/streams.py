from utilities.utils import *
from utilities.irc_utils import *
import socket
import random
import string
import threading
import os

def get_streams(game_id, number_of_results, user_id, user_login, language,cursor, endpoint):
    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    
    params = create_dict_from_vars(game_id=game_id, user_id=user_id, user_login=user_login, language=language)
    response_data, response_status = get_data_paginated(url, params, headers, number_of_results, cursor, {"data": []})

    if response_status != 200:
        return response_data, response_status
    
    for item in response_data["data"]:
        item.pop("type", None)
        item["stream_url"] = "https://www.twitch.tv/" + item["user_login"] #item.pop("user_login", None)
        item.pop("tag_ids", None)

    return response_data, response_status

def retrieve_comments_stop(crawling_id):
    # The crawling id is the same with TaskId
    irc = irc_connections.get(crawling_id)
    irc_thread = irc_threads.get(crawling_id)

    if irc_thread and irc:
        irc_thread.stop_flag = True
        irc.close()
        
        del irc_threads[crawling_id]
        del irc_connections[crawling_id]

        response_message, status_code = update_statuses(crawling_id)
        if status_code != 200:
            response_data = response_message
        
        response_data = {
            'id': crawling_id,
            'message': 'Connection stoped successfully'
        }
        print(response_data)
        return response_data, status_code
    else:
        response_data = {
            "id": crawling_id,
            'message': 'Connection not found. Please give a correct id'
        }
        return response_data, 404
    
irc_connections = {}
irc_threads = {}
def retrieve_comments_start(crawling_id, channels):
    # The crawling id is the same with the Task id
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
    print(f"The channels are {channels}")
    for channel, JobId in channels.items():
        send_command(irc, f'JOIN #{channel}')

    resp =  irc.recv(2048).decode()
    if 'failed' in resp:
        response_data = {
            'id': crawling_id,
            'message': resp
        }
        return response_data, 404
    
    irc_thread = threading.Thread(target=handle_messages, args=(irc, crawling_id, channels))
    irc_thread.start()
    
    irc_threads[crawling_id] = irc_thread
    irc_connections[crawling_id] = irc

    response_data = {
        'id': crawling_id,
        'channels': channels,
        'message': 'Connection started successfully'
    }
    return response_data, 200

def update_statuses(taskId):
    neo4j_url = os.getenv("NEO4J_URL")
    payload = {
        "id": taskId, 
        "status": "Completed"
    }
    res, status_code = make_request(f"{neo4j_url}/tasks", None, None,payload, "PATCH")
    if res.get('status') != "Success" or status_code != 200:
        return {'message': 'Failed to update task status', 'error': res}, status_code

    res, status_code = make_request(f"{neo4j_url}/jobs",{"taskId": taskId}, None, None, "GET")
    if res.get('status') != "Success" or status_code != 200:
        return {'message': 'Failed to retrieve jobs', 'error': res}, status_code
    
    jobs = res.get('data')
    for job in jobs:
        payload = {
            "id": job.get('id'),
            "status": "Completed"
        }
        res, status_code = make_request(f"{neo4j_url}/jobs", None, None, payload, "PATCH")
        if res.get('status') != "Success" or status_code != 200:
            return {'message': f'Failed to update job status for job ID {job.get("id")}', 'error': res}, status_code

    return {'message': 'All statuses updated successfully'}, 200