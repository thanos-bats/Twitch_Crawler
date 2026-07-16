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
        # Pop the incoming Twitch stream id and created_at from the payload (if present)
        channel.pop("id", None)
        channel.pop("createdAt", None)

        res, streamerName, status_code = create_job(channel, taskId)
        print(f"> Create job:\n {res}\n> Status code {status_code}\n\n")
        if res.get('error'):
            continue
        # Neo4j may return 'user_name' (hashed) rather than 'username'
        user_name = res.get("data", {}).get("user_name") or calculate_sha(streamerName)
        streamer_data["streamers"].append({
            "streamerName": user_name,
            # Use the original stream id as jobId for downstream consumers (e.g. Twitch_Ctrl)
            "jobId": res['data']['id'],
            "lan": res["data"]["lan"],
            "user_login": streamerName,
        })
    
    return streamer_data, status_code

def create_job(data, taskId):
    neo4j_url = (os.getenv("NEO4J_URL") or "").strip().rstrip("/")

    # The incoming payload now uses "username" and "url" etc. instead of "streamerName"/"urls".
    # We normalize here so the rest of the logic and the DB stay compatible.
    streamerName = data.get("username") or data.get("streamerName")

    data["taskId"] = taskId
    data["status"] = "Active"
    data["type"] = "twitch:stream"
    data["source"] = "twitch"
    data.pop("streamerName", None)
    data.pop("username", None)
    # Pseudo‑anonymize the username as 'user_name' (what Neo4j expects/returns)
    if streamerName:
        data["username"] = calculate_sha(streamerName)

    # return data, 202
    res, status_code = make_request(f"{neo4j_url}/jobs", None, None, data, "POST")
    if res.get('status') != "Success" or status_code != 200:
        return {'message': 'Failed to create Job', 'error': res}, None, status_code
    
    return res, streamerName, status_code

def get_streams(game_id, number_of_results, user_id, user_login, language, cursor, endpoint):
    # TODO: Add the language to the params
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
    connections = irc_connections.get(crawling_id)
    threads = irc_threads.get(crawling_id)
    # print(f"\n\n\n====================================================\nThreads {threads}")
    # print(f"Connections {connections}")
    if threads and connections:
        for irc_thread in threads: irc_thread.stop_flag = True
        for irc in connections: irc.close()
        
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
        task_info, status_code = get_task(crawling_id)
        if task_info["data"]['status'] == "Completed": 
            response_data = {
                "taskId": crawling_id,
                'message': 'Connection not found'
            }
            return response_data, 404
        
        response_data, status_code = update_statuses(crawling_id)
        return response_data, status_code
    
def send_command(irc, cmd):
    print(f'< {cmd}')
    irc.send((cmd + '\r\n').encode('utf-8'))

irc_connections = {}
irc_threads = {}
def retrieve_comments_start(caseId, crawling_id, channels): # The crawling id is the same with the Task id
    HOST = 'irc.chat.twitch.tv'
    PORT = 6667
    # print(f"CHANNERLS {channels}")
    if crawling_id not in irc_connections.keys():
        irc_connections[crawling_id] = []
    
    irc = socket.socket()
    irc.connect((HOST, PORT))
    irc_connections[crawling_id].append(irc)
    
    oauth_token = 'oauth:' + ''.join(random.choices(string.ascii_letters + string.digits, k=30))    # 'oauth:u800sfpa0b6nuaqsyg7queipflza5e'
    username = 'justinfan' + str(random.randint(1, 999))

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
    if crawling_id not in irc_threads: irc_threads[crawling_id] = []
    irc_threads[crawling_id].append(irc_thread)

    # print(irc_threads)
    # print(f'========================\n{irc_connections}')
    response_data = {
        'id': crawling_id,
        'channels': channels,
        'message': 'Connection started successfully'
    }
    return response_data, 200

def update_statuses(taskId):
    neo4j_url = (os.getenv("NEO4J_URL") or "").strip().rstrip("/")
    payload = {
        "id": taskId, 
        "status": "Completed"
    }
    res, status_code = make_request(f"{neo4j_url}/tasks", None, None,payload, "PATCH")
    if res.get('status') != "Success" or status_code != 200:
        return {'message': 'Failed to update task status', 'error': res}, status_code

    res, status_code = make_request(f"{neo4j_url}/jobs", {"taskId": taskId}, None, None, "GET")
    if res.get('status') != "Success" or status_code != 200:
        return {'message': 'Failed to retrieve jobs', 'error': res}, status_code

    # Response shape: {'status': 'Success', 'data': {'data': [<job dicts>], ...}}
    jobs_container = res.get('data') or {}
    jobs = jobs_container.get('data', []) or []

    for job in jobs:
        job_id = job.get('id')
        if not job_id:
            continue

        payload = {
            "id": job_id,
            "status": "Completed"
        }
        res, status_code = make_request(f"{neo4j_url}/jobs", None, None, payload, "PATCH")

        if res.get('status') != "Success" or status_code != 200:
            return {'message': f'Failed to update job status for job ID {job_id}', 'error': res}, status_code

    return {'message': 'All statuses updated successfully'}, 200

all_streams = {}
def get_all_tags(crawl_id, game_id, user_id, user_login, languages, endpoint):
    global all_streams
    tags_to_return = set()
    print(f"The crawl id is {crawl_id} | game_id {game_id}| languages {languages}")
    print(f"Currently saved crawl IDs: {list(all_streams.keys())}")
    if not crawl_id:
        # Check if game_id list and language match any existing crawl_id
        for existing_crawl_id, crawl_data in all_streams.items():
            # Get all languages from the existing crawl data
            existing_languages = set()
            for game_data in crawl_data.values():
                for streamers in game_data.values():
                    for streamer in streamers:
                        existing_languages.add(streamer.data.get('language', ''))
            
            # Check if both game_ids and languages match
            if set(crawl_data.keys()) == set(game_id) and set(languages) == existing_languages:
                print(f"Found matching crawl_id {existing_crawl_id} for game_ids {game_id} and languages {languages}")
                tags_to_return = set()
                for game_data in crawl_data.values():
                    tags_to_return.update(game_data.keys())
                return {"all_tags": list(tags_to_return), "crawl_id": existing_crawl_id}, 200

        # Keep only the last 3 crawl IDs
        if len(all_streams) >= 3:
            oldest_key = next(iter(all_streams))
            del all_streams[oldest_key]

        crawl_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        print(f"Random Id: {crawl_id}")
        print(f"Games {game_id}")
        new_games = game_id
        for game in game_id:
            if crawl_id not in all_streams:
                all_streams[crawl_id] = {}
            all_streams[crawl_id][game] = {}
        # return {"streams": all_streams, "crawl_id": crawl_id}, 200
    else:
        if crawl_id not in all_streams:
            all_streams[crawl_id] = {}
            print(f'The crawl id isnt exists. So I add it {all_streams[crawl_id]}')
            #return {"Error": "The crawl id there isn't exists"}, 404
        
        new_games = []
        for game in game_id:
            if game in all_streams[crawl_id]:
                tags_to_return.update(list(all_streams[crawl_id][game].keys()))
            else:
                new_games.append(game)

        print(f"The game ids list {game_id}")
        print(f"The new game ids are {new_games}")
        print(f"The tags to be returned 1: {tags_to_return}")
        if len(new_games) == 0:
            return {"all_tags": list(tags_to_return), "crawl_id": crawl_id}, 200 

    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }

    for language in languages:
        params = create_dict_from_vars(game_id=new_games, user_id=user_id, user_login=user_login, language=language)
        print(f"The params are {params}")
        response_data, response_status = get_data(url, params, headers, None, {"data": []})
        #print(f"For params \n{params}")
        if response_status != 200:
            return response_data, response_status
        
        for item in response_data["data"]:
            item.pop("type", None)
            item.pop("tag_ids", None)
            item["pseudo_user_login"] = calculate_sha(item["user_login"])
            item["stream_url"] = "https://www.twitch.tv/" + item["pseudo_user_login"]
            #print("Tags: ",item["tags"], " and user name ", item['user_login'] )

            if item["tags"] == None: continue
            normalized_tags = [tag.lower() for tag in item["tags"]]
            #print("Normalized Tags: ", normalized_tags, "\n----------------------\n")
            tags_to_return.update(normalized_tags)
            streamer = Streamer(item)
            for tag in normalized_tags:
                if int(item["game_id"]) not in all_streams[crawl_id]:
                    all_streams[crawl_id][int(item["game_id"])] = {}  # Initialize empty dict for the game_id if not present

                current_game_data = all_streams[crawl_id][int(item["game_id"])]
                # Now check for the tag and append the streamer
                if tag in current_game_data:
                    all_streams[crawl_id][int(item["game_id"])][tag].append(streamer)
                else:
                    all_streams[crawl_id][int(item["game_id"])][tag] = [streamer]
    
    # print(f"The all_streamers is {all_streams}\n")
    data = {"all_tags": list(tags_to_return), "crawl_id": crawl_id}
    # print(f"--------\nall streams {all_streams}\n---------\n")
    print(f"Saved crawl IDs after operation: {list(all_streams.keys())}")
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

    filtered_streamers = list({id(streamer): streamer for streamer in filtered_streamers}.values())
    
    data = {"data": []}
    for streamer in filtered_streamers:
        data["data"].append(streamer.to_dict())
    
    # Sort the data by viewer_count in descending order
    # data["data"].sort(key=lambda x: x.get('viewer_count', 0), reverse=True)
    
    return data, 200

def evaluate_expression(tokens, crawl_id, game_id):
    def apply_operator(operators, values):
        print(f"Current operators list inside the apply operator: {operators}\n")
        operator = operators.pop()
        if operator == 'and':
            right = values.pop()
            left = values.pop()
            print(f"left {left} \nright {right}")
            values.append(left & right)
        elif operator == 'or':
            right = values.pop()
            left = values.pop()
            values.append(left | right)
        elif operator == 'not':
            value = values.pop()
            # Retrieve all streamers for the game_id and remove those in value
            all_streamers = set(streamer for tag_streamers in all_streams[crawl_id][game_id].values() for streamer in tag_streamers)
            values.append(all_streamers - value)

    if crawl_id not in all_streams:
        return {"Error": "The crawl id doesn't exist"}, 404
    
    operators = []
    values = []
    while tokens:
        token = tokens.pop(0).strip()#.lower()
        print(f"The token is {token}")
        if token == '(':
            operators.append(token)
            print(f"Current operators list {operators}\n")
        elif token == ')':
            while operators and operators[-1] != '(':
                print(f"Current operators list {operators}\n")
                apply_operator(operators, values)
            operators.pop()  # Remove the '('
        elif token in {'and', 'or', 'not'}:
            while (operators and operators[-1] in {'and', 'or', 'not'} and (token != 'not' and operators[-1] != 'not')):
                apply_operator(operators, values)
            operators.append(token)
            print(f"Current operators list {operators}\n")
        else:
            streamers = set(get_streamers_for_keyword(game_id, token, crawl_id))
            print(f"Current operators list {operators}\n")
            print(f"For the game id {game_id}, the matched streamers for the token {token} are {len(streamers)}")
            values.append(streamers)
        
    while operators:
        apply_operator(operators, values)
    
    if len(values) == 0:
        return [], 200
    
    data = list(values[0])
    streamers = []
    for streamer in data:
        streamers.append(streamer.to_dict())

    return streamers, 200

def get_streamers_for_keyword(game_id, keyword, crawl_id):
    return all_streams[crawl_id].get(game_id, {}).get(keyword, set())

already_crawled = {}
def crawl_streams_background(case_id, task_id, game_ids, languages, tags):
    print(f"Into the background scheduler\nThe games {game_ids}\nlangs {languages}\ntags {tags}")
    
    data, status_code = get_all_tags(None, game_ids, None, None, languages, "/streams/")
    if status_code != 200: return data, status_code
    
    filtered_data = []
    for game_id in game_ids:
        tags_copy = tags[:]
        resp, status_code = evaluate_expression(tags_copy, data['crawl_id'], game_id)
        if status_code != 200: return resp, status_code
        filtered_data.extend(resp)

    if task_id not in already_crawled: already_crawled[task_id] = []

    to_crawl = {
        "streamers": []
    }
    
    if len(filtered_data) == 0: return 
    for streamer in filtered_data:
        if streamer['user_login'] in already_crawled[task_id]: continue
        already_crawled[task_id].append(streamer['user_login'])
        to_crawl["streamers"].append({
                                    "streamerName": streamer["user_login"], 
                                    "urls": [f"https://www.twitch.tv/{streamer['user_login']}"],
                                    "title": streamer['title'], 
                                    "keywords": streamer["tags"], 
                                    "lan": streamer['language'],
                                    "started_at": streamer['started_at']
                                })
    
    
    streamers_data, status_code = create_jobs_per_streamer(to_crawl.get("streamers"), task_id)
    if len(streamers_data["streamers"]) == 0:
        return get_error_message("No Job created into the DB")
    _, _ = retrieve_comments_start(case_id, task_id, streamers_data.get('streamers'))
    return

def remove_taskId_from_already_crawled(taskId):
    already_crawled.pop(taskId, None)

def get_task(taskId):
    neo4j_url = (os.getenv("NEO4J_URL") or "").strip().rstrip("/")
    res, status_code = make_request(f"{neo4j_url}/tasks",{"id": taskId}, None, None, "GET")
    return res, status_code

class Streamer:
    def __init__(self, data):
        self.data = data

    def to_dict(self):
        return self.data