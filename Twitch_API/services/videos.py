from utilities.utils import get_dotenv, get_data, create_dict_from_vars

def get_videos(game_id, number_of_results, user_id, endpoint, sorting_type):
    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    params = create_dict_from_vars(game_id=game_id, user_id=user_id, sort=sorting_type)

    # Fetch videos with correct argument order: after=None, data accumulator, first=number_of_results
    response_data, response_status = get_data(url, params, headers, None, {"data": []}, number_of_results)

    if response_status != 200:
        return response_data, response_status
    
    for item in response_data['data']:
        item['video_url'] = item.pop('url', None)
        item.pop('user_login', None)
        item.pop('viewable', None)
        item.pop('muted', None)

    return response_data, response_status
