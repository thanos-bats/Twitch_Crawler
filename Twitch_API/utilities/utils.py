# utilities/utils.py
import json
from flask import jsonify
import os
from dotenv import load_dotenv
import requests
from fuzzywuzzy import fuzz
import hashlib
import re

def parse_query(query):
    tokens = re.findall(r'\w+|\sAND\s|\sOR\s|\sNOT\s|\(|\)', query)
    lower_tokens = [token.lower() for token in tokens]
    return lower_tokens

def get_error_message(param):
    return jsonify({
        "error": "Bad Request",
        "status": 400,
        "message": f"The request must specify the {param} query parameter"
    }), 400

def get_dotenv():
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")
    base_url = os.getenv("BASE_URL")
    igdb_base_url = os.getenv("IGDB_URL")

    return client_id, access_token, base_url, igdb_base_url

def db_config():
    load_dotenv()
    db_client = os.getenv("MONGO_DB")
    db_name = os.getenv("MONGO_DB_NAME")
    collection_name = os.getenv("MONGO_COLLECTION_NAME")
    return db_client, db_name, collection_name

def load_dict_from_file(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle file not found or JSON parsing error
        return {"data": []}

def save_dict_to_json(games, filename):
    with open(filename, 'w') as file:
        json.dump(games, file, indent=4)

def make_request(url, params=None, headers=None, data=None, method="GET"):
    try:
        neo4j_url = os.getenv("NEO4J_URL")
        neo4j_token = os.getenv("NEO4J_TOKEN")
        if neo4j_url and neo4j_token and url.startswith(neo4j_url):
            headers = headers.copy() if headers else {}
            headers.setdefault("Authorization", f"Bearer {neo4j_token}")

        if method.upper() == 'GET':
            response = requests.get(url, params=params, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, headers=headers)
        else:
            # Add more cases for other HTTP methods as needed
            raise ValueError(f"Unsupported HTTP method: {method}")
        response.raise_for_status()
        response_data = {
        'status': 'Success',
        'data': response.json()  # Assuming the response contains JSON data
        }
        return response_data, 200
    
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            error_data = e.response.json()
            status_code = e.response.status_code
        else:
            error_data = {
                'status': 'Error',
                'message': str(e)
            }
            status_code = 500

        return error_data, status_code
    
    except ValueError as e:
        error_data = {
            'status': 'Error',
            'message': 'JSON Decoding Error'
            }
        return error_data, 500

def pagination_handler(json_data, number, len_data):
    remaining_number = number - len_data
    if remaining_number > 0:
        if ("pagination" in json_data) and ("cursor" in json_data["pagination"]) and (json_data["pagination"].get("cursor")):
            return True    
        
    return False

def handle_first_param(first, number):
    if number < first:
        return number, 0
    
    return 100, (number - first)

def get_data(url, params, headers, after=None, data={"data": []}, first=100, times=0):
    # if params["language"] == 'en':
    times = times + 1
    
    params["first"] = first
    if after is not None:
        params["after"] = after

    response, status_code = make_request(url, params, headers)

    if status_code != 200 and (not data["data"]): # If there is an error, we return the error
        return response, status_code
    
    json_data = response['data']
    if not json_data.get("data") and not data["data"]:
        return data, status_code

    if not json_data:
        return data, status_code
    
    data["data"].extend(json_data["data"])

    if not json_data["pagination"]:
        return data, status_code
    
    after = json_data["pagination"]["cursor"]        
    if times >= 5: return data, status_code
    return get_data(url, params, headers, after=after, data=data, times=times)

def get_data_paginated(url, params, headers, number, after=None, data={"data": []}, first=100):
    params["first"], number = handle_first_param(first, number)
    if after is not None:
        params["after"] = after
    
    response, status_code = make_request(url, params, headers)
    print(url)
    if status_code != 200 and (not data["data"]): # If there is an error, we return the error
        return response, status_code

    json_data = response['data']
    
    return json_data, status_code

def create_dict_from_vars(**kwargs):
    params = {key: value for key, value in kwargs.items() if value is not None}
    return params

def calculate_similarity(query, target):
    return fuzz.ratio(query, target)

def detect_language(streamer, msg):
    data = [{"id": streamer, "content": msg}]
    resp, resp_status_code = make_request(os.getenv("LANG_DETECT_URL"), None, None, data, "POST")
    if resp_status_code != 200:
        return {"error": "Error with the language detection of the message content"}
    
    detect_data = {}
    for item in resp['data']:
        id_ = item.get("id")
        if "detection" in item:
            languages = item["detection"]["languages"]
            if languages:
                languages.sort(key=lambda x: x["percent"], reverse=True)
                language = languages[0]["code"]
                if language not in {"el", "en"}: # For now the Tools are support Greek and English content. For multilingual content delete those lines
                    language = "und"
            else:
                language = "und"

        else:
            language = "und" if "error" in item else None

        detect_data[id_] = language
    return detect_data

def calculate_sha(input):
    input_bytes = input.encode('utf-8')
    sha512_hash = hashlib.sha512(input_bytes)
    sha512_hex = sha512_hash.hexdigest()

    return sha512_hex

