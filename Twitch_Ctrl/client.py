import os
import json
import datetime
import requests
import hashlib
import re
import random
import time

from socketio.client import Client
from dotenv import load_dotenv
from kafka.kafka_producer import ProducerHandler

load_dotenv()

class SocketClient:
    def __init__(self):
        self.socket = Client()
        # self.producer = ProducerHandler()

        self.socket.on('connect', self.handle_connect)
        self.socket.on('disconnect', self.handle_disconnect)
        self.socket.on('message', self.handle_message)

    def handle_connect(self):
        print('Connection established')

    def handle_disconnect(self):
        print('You disconnect from the server')

    def start(self):
        socket_url = os.getenv('SOCKET_URL')
        # Retry until twitch_api is reachable (handles container start-up race).
        while True:
            try:
                print(f"Connecting to {socket_url}")
                self.socket.connect(socket_url)
                self.socket.wait()
                break
            except Exception as e:
                print('> Error connecting: ', e)
                print('> Retrying in 5 seconds...')
                time.sleep(5)
    
    def handle_message(self, data):
        # Data's structure { "data": {Message content}, "channels": [{"streamerName": Name, "jobId": id, "lan": Language}], "caseId": caseId, "taskId": taskId}
        sha_data = pseudo_anonymize(data)

        streamer_name = sha_data['data']['streamer']
        msg_data = sha_data.get('data')
        hash_streamer_name = msg_data.get('streamer', 'unknown_streamer')
        channels = data.get('channels')
        caseId = data.get('caseId')
        taskId = data.get('taskId')

        # Try to resolve jobId by matching hashed streamer name; if that fails,
        # fall back to the first channel's jobId so we never leave jobId undefined.
        jobId = None
        if channels:
            for idx, streamer_data in enumerate(channels):
                chan_name = streamer_data.get('streamerName')
                if chan_name == streamer_name:
                    jobId = streamer_data.get('jobId')
                    print(f"[handle_message] MATCH on index {idx}, jobId={jobId}")
                    break

            if jobId is None:
                # Fallback: use the first channel's jobId
                print("[handle_message] WARNING: No channel matched hashed streamer; "
                      "falling back to first channel jobId.")
                jobId = channels[0].get('jobId')
        else:
            print("[handle_message] ERROR: No channels provided in message; cannot determine jobId.")
            return

        document_data = {
            "jobId": jobId,
            "domainId": f"twitch:comment:{hash_streamer_name}",
            "title": None,
            "content": msg_data.get("message"),
            "raw": None,
            "source": "twitch",
            "type": "twitch:comment",
            "publishedAt": msg_data.get("created_at"),
            "discoveredAt": msg_data.get("created_at"),
            "lan": msg_data.get("lang"),
            "attributes": {
                "authorName": msg_data['username'],
                "authorColor": get_random_color()
            }
        }
        
        entity_data = {
            "domainId":f"twitch:profile:{msg_data['username']}",
            "title":None,
            "name":msg_data.get("username"),
            "source":"twitch",
            "type":"twitch:profile",
            "discoveredAt": msg_data.get("created_at")
        }
        
        try:
            neo4j_base = (os.getenv("NEO4J_URL") or "").strip().rstrip("/")
            document_response, document_response_status = make_request(f"{neo4j_base}/documents/SocialMedia", None, None, document_data, "POST")
            entity_response, entity_response_status  = make_request(f"{neo4j_base}/entities", None, None, entity_data, "POST")
            if document_response_status not in (200, 201) or entity_response_status not in (200, 201):
                print(f"Failed to persist comment: document={document_response_status} {document_response}, "
                      f"entity={entity_response_status} {entity_response}")
                return
            
            docId = document_response['data']['id']
            entityId = entity_response['data']['id']
            relationship_data = {
                "sourceNodeId": docId,
                "targetNodeId": entityId,
                "type": "hasAuthor"
            }
            
            _, _ = make_request(f"{neo4j_base}/relationships", None, None, relationship_data, "POST")

            # self.send_message_to_kafka(streamer_name, caseId, taskId, jobId, docId)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def generate_message_results(self, sentUtc, streamer, caseId, taskId, jobId, documentId):
        msg = {
            "header": {
                "topicName":os.getenv("TOPIC_MESSAGE_DONE"),
                "msgId": documentId,
                "sender": "CERTH",
                "source": "Twitch",
                "sentUtc": sentUtc
            },
            "body": {
                "data": [
                    {
                        "documentId": documentId,
                        "caseId": caseId,
                        "taskId": taskId,
                        "jobId": jobId
                    }
                ]
            }
        }

        return os.getenv("TOPIC_MESSAGE_DONE"), msg

    def send_message_to_kafka(self, streamer_name, caseId, taskId, jobId, docId):
        topic, message = self.generate_message_results(
            datetime.datetime.utcnow().isoformat().split(".")[0] + 'Z',
            streamer_name,
            caseId, 
            taskId, 
            jobId, 
            docId)
        self.producer.send_message(topic, message)

def _safe_response_json(response):
    """Parse JSON body; return a dict describing non-JSON/empty bodies."""
    text = (response.text or "").strip()
    if not text:
        return {
            "status": "Error",
            "message": "Empty response body",
            "http_status": response.status_code,
        }
    try:
        return response.json()
    except ValueError:
        return {
            "status": "Error",
            "message": "Non-JSON response body",
            "http_status": response.status_code,
            "body_preview": text[:300],
        }


def make_request(url, params=None, headers=None, data=None, method="GET"):
    try:
        # Automatically attach Neo4j bearer token for Neo4j requests.
        # The token is fetched from the Twitch_API service, which is
        # responsible for generating and refreshing it.
        neo4j_url = (os.getenv("NEO4J_URL") or "").strip()
        if neo4j_url and url.startswith(neo4j_url):
            headers = headers.copy() if headers else {}

            neo4j_token = get_neo4j_token()
            if neo4j_token:
                headers.setdefault("Authorization", f"Bearer {neo4j_token}")
            else:
                print("WARNING: Could not obtain Neo4j token; proceeding without Authorization header.")

        if method.upper() == 'GET':
            response = requests.get(url, params=params, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PATCH':
            response = requests.patch(url, json=data, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        response_data = {
            'status': 'Success',
            'data': _safe_response_json(response)
        }
        # If the success path still got a non-JSON body, treat as failure.
        if isinstance(response_data['data'], dict) and response_data['data'].get('status') == 'Error':
            print(f"Request to {url} returned non-JSON success body: {response_data['data']}")
            return response_data['data'], response.status_code
        return response_data, response.status_code
    
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            error_data = _safe_response_json(e.response)
            status_code = e.response.status_code
        else:
            error_data = {
                'status': 'Error',
                'message': str(e)
            }
            status_code = 500
        print(f"The error data is {error_data} with status {status_code} (url={url})")
        return error_data, status_code
    
    except ValueError as e:
        error_data = {
            'status': 'Error',
            'message': f'JSON Decoding Error: {e}'
            }
        return error_data, 500
    

def get_neo4j_token() -> str | None:
    provider_url = os.getenv("NEO4J_TOKEN_PROVIDER_URL")

    # First, try the provider endpoint (recommended in docker-compose).
    if provider_url:
        try:
            resp = requests.get(provider_url, timeout=5)
            resp.raise_for_status()
            body = resp.json()
            token = body.get("token")
            if token:
                return token
            print(f"WARNING: Token provider response missing 'token' field: {body}")
        except Exception as e:
            print(f"WARNING: Failed to fetch Neo4j token from provider {provider_url}: {e}")

    # Fallback: use static env value, if present.
    fallback = os.getenv("NEO4J_TOKEN")
    if not fallback:
        print("WARNING: No NEO4J_TOKEN available in environment.")
        return None
    return fallback

def pseudo_anonymize(data):
    streamer_hash = calculate_sha(data['data']['streamer'])
    data['data']['streamer'] = streamer_hash

    username_hash = calculate_sha(data['data']['username'])
    data['data']['username'] = username_hash

    message = data['data']['message']
    mentions = re.findall(r'@[^\s]+', message) 
    for mention in mentions:
        mention_hash = calculate_sha(mention[1:])
        message = message.replace(mention, '@'+mention_hash)

    data['data']['message'] = message
    return data

def calculate_sha(input):
    input_bytes = input.encode('utf-8')
    sha512_hash = hashlib.sha512(input_bytes)
    sha512_hex = sha512_hash.hexdigest()

    return sha512_hex

def get_random_color():
    letters = '0123456789ABCDEF'
    color = '#'
    for i in range(6):
        color += letters[random.randint(0, 15)]
    return color

if __name__ == '__main__':
    socket_client = SocketClient()
    socket_client.start()
