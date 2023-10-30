from utilities.utils import get_dotenv, make_request, save_dict_to_json, create_dict_from_vars
from utilities.db_utils import multiple_update_db, get_exact_match, get_text_index

def search_games_by_keyword(keyword, limit):
    return get_text_index(keyword, limit)

def get_games(after, games):
    client_id, access_token, base_url, _ = get_dotenv()
    endpoint = "games/top"
    url = f"{base_url}/{endpoint}"
    params = {"first": 100}
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }

    if after is None:
        print(headers)
    if after is not None:
        params["after"] = after

    response, status_code = make_request(url, params, headers)

    if (status_code == 500) and (not games["data"]):
        print(f'{response}')
        return

    if response['data']:
        json_data = response['data']
        games["data"].extend(json_data["data"])

        if ("pagination" in json_data) and ("cursor" in json_data["pagination"]) and (json_data["pagination"].get("cursor")):
            after = json_data["pagination"]["cursor"]

            return get_games(after, games)
        else: 
            save_dict_to_json(games, 'games.json')
            multiple_update_db(games, "id")
            
    else:
        save_dict_to_json(games, 'games.json')
        multiple_update_db(games, "id")

def get_game_search(game_id):
    query = create_dict_from_vars(id=game_id)
    result = get_exact_match(query)
    
    return result
