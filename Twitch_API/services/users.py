from utilities.utils import get_dotenv, create_dict_from_vars, make_request

def get_user(user_name, user_id, endpoint):
    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"
    params = create_dict_from_vars(id=user_id, login=user_name)
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    print(f"The headers are {headers}")
    response, status_code = make_request(url, params, headers)
    if status_code != 200:
        return response, status_code
    
    return response['data'], status_code
    