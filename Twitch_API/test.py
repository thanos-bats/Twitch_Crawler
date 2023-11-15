import time
import os
import json
from utilities.utils import *
from utilities.irc_utils import *
from flask import jsonify
import requests
import json
import random

game_ids = [509658, 23020, 33214, 510218, 497497]
minecraft_ids = [27471, 512663, 290655618, 1900455944, 509725, 1374264548, 437143927, 1094371038, 1594527138, 1175133722, 1817240123, 490130, 1078970694]
lego_ids = [1612, 2233, 1053546950, 21344, 417713, 8737, 2024234285, 4245, 342604747, 514490, 10253, 494160368, 505211, 489458, 514398, 1023847808, 22522, 20355, 489766, 513160]
fifa_ids = [24408, 415872, 369095, 518204, 1745202732, 495589, 14628, 1869092879, 496320, 489608, 506103, 14015, 512804, 387707425, 936351243, 493091, 462027567, 27333, 460402, 558089024]
football_manager_ids = [311695767, 27159, 12685, 27716, 514816, 1047410718, 1406346985, 509802, 24656, 356714198, 1554396169, 21318, 1271244884, 1310625753, 1687308906, 586622463, 661619119, 1207189138, 1532602910, 235860302]

madfut = 83746781
stumble_guys = 1312214340

languages = ['el']
number_of_results = 50

def get_streams(game_id, number_of_results, user_id, language, endpoint):
    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    
    params = create_dict_from_vars(game_id=game_id, user_id=user_id, language=language)
    response_data, response_status = get_data(url, params, headers, number_of_results, None, {"data": []})

    if response_status != 200:
        return response_data, response_status
    
    for item in response_data["data"]:
        item.pop("type", None)
        item["stream_url"] = "https://www.twitch.tv/" + item["user_login"] #item.pop("user_login", None)
        item.pop("tag_ids", None)

    return response_data, response_status

def make_api_calls(game_ids):
    try:
        for game_id in game_ids:
            for language in languages:
                response_data, response_status = get_streams(game_id, number_of_results, None, language, "/streams")

                if response_status == 200:
                    if len(response_data['data']) == 0:
                        # print(f'the game {game_id} has no data for language {language}')
                        continue
                    
                    process_streams(response_data, game_id, language)
                else:
                    print(f'API cal for game id {game_id} and language {language} failed with status code {response_status}')

        print('Finished api calls')
    except Exception as e:
        print(f'An error occurred: {str(e)}')

def get_greek_streams():
    # try:
        for language in languages:
            response_data, response_status = get_streams(None, 300, None, language, '/streams')
            print(len(response_data), response_status)
            if response_status == 200:
                if len(response_data['data']) == 0:
                    #print(f'the game {game_id} has no data for language {language}')
                    continue
                
                process_streams(response_data, '_', language)
            else:
                print(f'API cal for and language {language} failed with status code {response_status}')

        print('Finished api calls')
    # except Exception as e:
    #     print(f'An error occurred: {str(e)}')

def process_streams(streams_data, game_id, language):
    flag_terms = ["girl", "boy", "daddy", "chat", "chill", "relax", "χαλαρ"]

    # Filter streams based on tags
    filtered_streams = [
        stream for stream in streams_data.get("data", [])
        if stream.get('tags') and any(flag.lower() in ' '.join(map(str.lower, stream['tags'])) for flag in flag_terms)
    ]
    
    if filtered_streams:
        print('Starting crawling')
        start_crawling(filtered_streams)
    else:
        print('No filtered streams to save.')

def start_crawling(filtered_streams):
    api_url = "http://localhost:3000/streams/comments/start"
    headers = {"Content-Type": "application/json"}
    streamer_names = []
    random_id = str(random.randint(1, 1000))

    for stream in filtered_streams:
        streamer_name = stream.get('user_login', '')
        
        if streamer_name not in started_crawling_streamers:
            streamer_names.append(streamer_name)
            started_crawling_streamers[streamer_name] = random_id
        else:
           print(f"The streamer {streamer_name} is already crawled") 

    payload = {
        "streamers": streamer_names,
        "id":  random_id
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)

        if response.status_code // 100 == 2:
            print("Successfully started comments for all streamers")
            print(response.text)
        else:
            print(f"Failed to start comments. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {str(e)}")

def get_ids_by_keyword(keyword):
    url = "http://localhost:3000/games"
    params = {"keyword": keyword}
    headers = {"Content-Type": "application/json"}

    response_data, status_code = make_request(url, params, headers)
    if status_code == 200:
        i = 0
        for game in response_data['data']['data']:
            if game.get('score', 0) >= 0.75:
                i += 1

        print(f"Total games with score >= 0.75 (using loop): {i}")

        result_list = [item['id'] for item in response_data['data']['data'] if item.get('score', 0) >= 0.75]

        print(f"Total games with score >= 0.75 (using list comprehension): {len(result_list)}")
        return result_list
    
    return response_data

keywords = ['fortnite', 'Minecraft', 'Stardoll', 'Roblox', 'Fall Guys', 'Rocket league', 'sims', 'fifa', 'NBA', 'just chatting', 'League of Legends', 'Brawl Stars']
keywords = ['just chatting', 'league of legends']
game_ids = [id for keyword in keywords for id in get_ids_by_keyword(keyword)]
flag_terms = [
        "girl",
        "boy",
        "daddy",
        "chat",
        "chill",
        "relax",
        "χαλαρ"
    ]

started_crawling_streamers = {}
while True:
    make_api_calls(game_ids)
    print(started_crawling_streamers)

    time.sleep(3600)