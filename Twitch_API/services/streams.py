from utilities.utils import *
from utilities.irc_utils import *
import socket
import random
import string
import threading
import os

def create_jobs_per_streamer(channels, taskId):
    streamer_data = {
        "streamers": []
    } 
    for channel in channels:
        res, streamerName, status_code = create_job(channel, taskId)
        if res.get('status') != "Success":
            continue
        streamer_data["streamers"].append({"streamerName": res["data"]["user_name"], "jobId": res["data"]["id"], "lan": res["data"]["lan"], "user_login": streamerName})
       
    return streamer_data, status_code

def create_job(data, taskId):
    neo4j_url = os.getenv("NEO4J_URL")
    data["taskId"] = taskId
    data["status"] = "Active"
    data["type"] = "twitch:crawl"
    streamerName = data.get("streamerName")
    data["user_name"] = calculate_sha(data.pop("streamerName"))
    # return data, 202
    res, status_code = make_request(f"{neo4j_url}/jobs", None, None, data, "POST")
    if res.get('status') != "Success" or status_code != 200:
        return {'message': 'Failed to create Job', 'error': res}, None, status_code
    
    return res, streamerName, status_code

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
    
    all_tags = set()
    for item in response_data["data"]:
        item.pop("type", None)
        item.pop("tag_ids", None)
        item["pseudo_user_login"] = calculate_sha(item["user_login"])
        item["stream_url"] = "https://www.twitch.tv/" + item["pseudo_user_login"] #item.pop("user_login", None)
        all_tags.update(item.get("tags", []))

    response_data["all_tags"] = list(all_tags)
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
        else:
            response_data = {
                'id': crawling_id,
                'message': 'Connection stoped successfully'
            }
            status_code = 200

        return response_data, status_code
    else:
        response_data = {
            "taskId": crawling_id,
            'message': 'Connection not found. Please give a correct id'
        }
        return response_data, 404
    
def send_command(irc, cmd):
    print(f'< {cmd}')
    irc.send((cmd + '\r\n').encode('utf-8'))

irc_connections = {}
irc_threads = {}
def retrieve_comments_start(caseId, crawling_id, channels):
    
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
    
    for channel in channels:
        send_command(irc, f"JOIN #{channel.pop('user_login')}")
        
    resp =  irc.recv(2048).decode()
    if 'failed' in resp:
        response_data = {
            'id': crawling_id,
            'message': resp
        }
        return response_data, 404
    
    irc_thread = threading.Thread(target=handle_messages, args=(irc, crawling_id, channels, caseId))
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

all_streams = {}
def get_all_tags(crawl_id, game_id, user_id, user_login, languages, endpoint):
    global all_tags
    tags_to_return = set()
    if not crawl_id:
        all_streams.clear()

        crawl_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        print(f"Random Id: {crawl_id}")
        print(f"Games {game_id}")
        for game in game_id:
            if crawl_id not in all_streams:
                all_streams[crawl_id] = {}
            all_streams[crawl_id][game] = {}
        # return {"streams": all_streams, "crawl_id": crawl_id}, 200
    else:
        if crawl_id not in all_streams:
            return {"Error": "The crawl id there isn't exists"}, 404
        
        new_games = []
        for game in game_id:
            if game in all_streams[crawl_id]:
                tags_to_return.update(list(all_streams[crawl_id][game].keys()))
            else:
                new_games.append(game)

        print(f"The game ids list {game_id}")
        print(f"The new game ids are {new_games}")
        print(f"The tags to be returned {tags_to_return}")
        if len(new_games) == 0:
            return {"all_tags": list(tags_to_return), "crawl_id": crawl_id}, 200 

    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }

    for language in languages:
        params = create_dict_from_vars(game_id=game_id, user_id=user_id, user_login=user_login, language=language)

        response_data, response_status = get_data(url, params, headers, None, {"data": []})

        if response_status != 200:
            return response_data, response_status
        print(f"The all_streamers is {all_streams}\n")
        for item in response_data["data"]:
            item.pop("type", None)
            item.pop("tag_ids", None)
            item["pseudo_user_login"] = calculate_sha(item["user_login"])
            item["stream_url"] = "https://www.twitch.tv/" + item["pseudo_user_login"]
            print("Tags: ",item["tags"], " and user name ", item['user_login'] )
            if item["tags"] == None: continue
            tags_to_return.update(item["tags"])
            streamer = Streamer(item)
            for tag in item["tags"]:
                if int(item["game_id"]) not in all_streams[crawl_id]:
                    all_streams[crawl_id][int(item["game_id"])] = {}  # Initialize empty dict for the game_id if not present

                current_game_data = all_streams[crawl_id][int(item["game_id"])]

                # Now check for the tag and append the streamer
                if tag in current_game_data:
                    all_streams[crawl_id][int(item["game_id"])][tag].append(streamer)
                else:
                    all_streams[crawl_id][int(item["game_id"])][tag] = [streamer]
    
    print(f"The all_streamers is {all_streams}\n")
    data = {"all_tags": list(tags_to_return), "crawl_id": crawl_id}
    return data, 200

def get_streams_by_tags(tags, crawl_id, game_ids):
    if crawl_id not in all_streams:
        return {"Error": "The crawl id there isn't exists"}, 404
    filtered_streamers = []
    for game_id, tags_data in all_streams[crawl_id].items():
        if game_id not in game_ids: 
            continue
        
        for tag in tags:
            if tag in tags_data:
                filtered_streamers.extend(tags_data[tag])
    print(filtered_streamers)

    filtered_streamers = list({id(streamer): streamer for streamer in filtered_streamers}.values())
    data = {"data": []}
    for streamer in filtered_streamers:
        data["data"].append(streamer.to_dict())
    
        
    return data, 200

class Streamer:
    def __init__(self, data):
        self.data = data

    def to_dict(self):
        return self.data