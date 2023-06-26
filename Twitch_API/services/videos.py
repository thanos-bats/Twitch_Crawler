from utilities.utils import get_dotenv, get_data, create_dict_from_vars

def get_videos(game_id, number_of_results, user_id, endpoint, sorting_type):
    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"

    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    params = create_dict_from_vars(game_id=game_id, user_id=user_id, sort=sorting_type)
    print(f'Headers {headers}' )
    print(f'params {params}')
    print()
    response_data, response_status = get_data(url, params, headers, number_of_results, None, {"data": []})
    for item in response_data['data']:
        item['video_url'] = item.pop('url', None)
        item.pop('user_login', None)
        item.pop('viewable', None)
        item.pop('muted', None)

    return response_data, response_status
