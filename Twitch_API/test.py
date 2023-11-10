import time
import os
import json
from utilities.utils import get_dotenv, get_data, create_dict_from_vars
from utilities.irc_utils import *
from flask import jsonify

game_ids = [509658, 23020, 33214, 510218, 497497]
minecraft_ids = [27471, 512663, 290655618, 1900455944, 509725, 1374264548, 437143927, 1094371038, 1594527138, 1175133722, 1817240123, 490130, 1078970694]
lego_ids = [1612, 2233, 1053546950, 21344, 417713, 8737, 2024234285, 4245, 342604747, 514490, 10253, 494160368, 505211, 489458, 514398, 1023847808, 22522, 20355, 489766, 513160]
fifa_ids = [24408, 415872, 369095, 518204, 1745202732, 495589, 14628, 1869092879, 496320, 489608, 506103, 14015, 512804, 387707425, 936351243, 493091, 462027567, 27333, 460402, 558089024]
football_manager_ids = [311695767, 27159, 12685, 27716, 514816, 1047410718, 1406346985, 509802, 24656, 356714198, 1554396169, 21318, 1271244884, 1310625753, 1687308906, 586622463, 661619119, 1207189138, 1532602910, 235860302]

madfut = 83746781
stumble_guys = 1312214340

languages = ['el']
number_of_results = 50
endpoint = '/streams'

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

def make_api_calls():
    try:
        for game_id in game_ids + minecraft_ids + lego_ids + fifa_ids + football_manager_ids:
            for language in languages:
                response_data, response_status = get_streams(game_id, number_of_results, None, language, endpoint)

                if response_status == 200:
                    if len(response_data['data']) == 0:
                        #print(f'the game {game_id} has no data for language {language}')
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
            response_data, response_status = get_streams(None, 300, None, language, endpoint)
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
    # Define the base directory
    # Ensure that the 'twitch_results' directory exists
    base_directory = 'twitch_results'
    os.makedirs(base_directory, exist_ok=True)

    timestamp = time.strftime("%d%m-%H%M")
    file_name = f"{timestamp}_{game_id}_{language}.json"

    file_path = os.path.join(base_directory, file_name)

    print(f'the file {file_name} saved')

    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(streams_data, json_file, ensure_ascii=False, indent=4)

while True:
    #make_api_calls()
    get_greek_streams()
    time.sleep(3600)