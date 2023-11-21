import time
from utilities.utils import *
from utilities.irc_utils import *
import requests
import random

languages = ['el']
number_of_results = 50

def make_api_calls(game_ids):
    api_url = "http://localhost:3000/streams"
    headers = {"Content-Type": "application/json"}
    chunk_size = 100  # Set the chunk size

    try:
        for i in range(0, len(game_ids), chunk_size):
            # Extract a chunk of game IDs
            chunk = game_ids[i:i+chunk_size]
            print(len(chunk))
            game_ids_param = ','.join(map(str, chunk))
            print(f"Processing game IDs: {game_ids_param}")

            for language in languages:
                response = requests.get(api_url, params={'game_id': game_ids_param, 'language': language}, headers=headers)

                if response.status_code // 100 != 2:
                    print(f"Failed to get streams. Status code: {response.status_code}")
                    return
                
                print(f"Successfully get streams with status {response.status_code}")
                process_streams(response.json())

    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {str(e)}")

def process_streams(streams_data):
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
    current_timestamp = int(time.time())
    random_component = random.randint(1, 1000)
    random_id = f"{current_timestamp}_{random_component}"

    for stream in filtered_streams:
        streamer_name = stream.get('user_login', '')
        tags = set(stream.get('tags', []))
        title = stream.get('title', '')
        
        if streamer_name not in started_crawling_streamers:
            print(f"I m starting crawling for the streamer {streamer_name} for the game {stream.get("game_name")}")
            streamers_data[streamer_name] = {'tags': tags, 'titles': {title}}
            streamer_names.append(streamer_name)
            started_crawling_streamers[streamer_name] = random_id
        else:
            print(f"The streamer {streamer_name} is already crawled")
            streamers_data[streamer_name]['tags'].update(tags)
            streamers_data[streamer_name]['titles'].add(title)

    if streamer_names:
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

    for user_name, data in streamers_data.items():
        data['tags'] = list(data['tags'])
        data['titles'] = list(data['titles'])

    save_streamers_data_to_file(streamers_data)

def save_streamers_data_to_file(streamers_data):
    parent_folder = os.path.abspath(os.path.join(os.getcwd(), os.pardir))  # Get the parent folder

    data_folder = os.path.join(parent_folder, 'data')
    os.makedirs(data_folder, exist_ok=True)

    file_path = os.path.join(data_folder, 'streamers_data.json')

    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(streamers_data, json_file, indent=2, ensure_ascii=False)

def get_ids_by_keyword(keyword):
    url = "http://localhost:3000/games"
    params = {"keyword": keyword}
    headers = {"Content-Type": "application/json"}

    response_data, status_code = make_request(url, params, headers)
    if status_code == 200:
        result_list = [item['id'] for item in response_data['data']['data'] if item.get('score', 0) >= 0.75]

        print(f"Total games with score >= 0.75 (using list comprehension): {len(result_list)} for keyword {keyword}")
        return result_list
    
    return response_data

keywords = ['fortnite', 'Minecraft', 'Stardoll', 'Roblox', 'Fall Guys', 'Rocket league', 'sims', 'fifa', 'NBA', 'just chatting', 'League of Legends', 'Brawl Stars']
# game_ids = [id for keyword in keywords for id in get_ids_by_keyword(keyword)]
game_ids= ['33214', '27471', '509725', '290655618', '1374264548', '1900455944', '512663', '1977715177', '23020', '511385', '512980', '1876375884', '395103912', '982652570', '417909', '98005', '1665792426', '216753271', '518417', '1607030483', '1345939041', '515055', '40756625', '1434152292', '513557', '1367213437', '1087122443', '513010', '272274438', '1795888329', '30921', '1270322937', '1212268058', '78248334', '163116623', '24591', '558525694', '36169590', '510439', '2959', '705474562', '1442649095', '509896', '581731159', '414005931', '2022942133', '552024577', '503399', '65851346', '627043847', '621804855', '16027', '263271811', '1871539368', '1908612693', '24700', '1706347804', '20417', '7582', '494516', '12883', '18814', '1428668531', '2085809397', '10868', '369252', '1433181496', '556191994', '2065602786', '355815731', '24408', '387707425', '27333', '489608', '14015', '506103', '496320', '369095', '1745202732', '493091', '936351243', '495589', '1869092879', '14628', '462027567', '415872', '558089024', '518204', '512804', '460402', '4236', '492901', '21628', '696', '233693544', '1371363232', '28310', '19469', '19555', '387', '9024', '9470', '18507', '24310', '489812', '459445', '31662', '503729', '489262', '518023', '509658', '333674999', '25122', '582894905', '1505280121', '754406904', '219069246', '1218372368', '494818157', '616334595', '313084', '1307366101', '1335496647', '1865730492', '2029953834', '195947496', '23951866', '498247', '1981613962', '16652', '21779', '1583577433', '515472', '522761732', '52111426', '514858', '2120585932', '192621714', '515478', '13215', '1324180952', '2018553853', '510439', '950700654', '2124292874', '274', '497170', '30921', '21678', '1111525476', '497497', '1370940026', '1273054776', '92925', '1522459892', '2132875221', '489575', '1921908933', '458290', '491832', '509513', '576498568', '25994', '330883277', '7467', '709121415', '2006666188', '787643659', '1365999732', '2080146678']
print(f"the length of game ids are {len(game_ids)}")

flag_terms = [
        "girl",
        "boy",
        "daddy",
        "chat",
        "chill",
        "relax",
        "χαλαρ"
    ]

streamers_data = {}
started_crawling_streamers = {}
while True:
    make_api_calls(game_ids)
    print(started_crawling_streamers)

    time.sleep(3600)