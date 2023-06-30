# utilities/utils.py
import json
from flask import jsonify
import os
from dotenv import load_dotenv
import requests
import random

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

def make_request(url, params, headers):
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        response_data = {
        'status': 'Success',
        'data': response.json()  # Assuming the response contains JSON data
        }
        return response_data, 200
    
    except requests.exceptions.RequestException as e:
        # Handle request exceptions (e.g., network error, connection timeout)
        error_data = {
        'status': 'Error',
        'message': str(e)
        }
        return error_data, 500
    
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

def get_data(url, params, headers, number, after=None, data={"data": []}, first=100):
    params["first"], number = handle_first_param(first, number)
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
    if number == 0:
        return data, status_code
    
    after = json_data["pagination"]["cursor"]

    return get_data(url, params, headers, number, after=after, data=data)

def create_dict_from_vars(**kwargs):
    params = {key: value for key, value in kwargs.items() if value is not None}
    return params
