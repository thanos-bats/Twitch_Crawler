from utilities.utils import get_dotenv, create_dict_from_vars, make_request

def get_user(user_name, user_id, endpoint):
    client_id, access_token, base_url, _ = get_dotenv()
    url = f"{base_url}{endpoint}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    params = create_dict_from_vars(id=user_id, login=user_name)
    print()
    response, error = make_request(url, params, headers)
    if error:
        return error, error['status']
    
    return response.json(), response.status_code
    