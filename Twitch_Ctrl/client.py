import os
import json
import datetime
import requests
import hashlib
import re

from socketio.client import Client
from dotenv import load_dotenv
from kafka.kafka_producer import ProducerHandler

load_dotenv()

class SocketClient:
    def __init__(self):
        self.socket = Client()
        self.producer = ProducerHandler()

        self.socket.on('connect', self.handle_connect)
        self.socket.on('disconnect', self.handle_disconnect)
        self.socket.on('message', self.handle_message)

    def handle_connect(self):
        print('Connection established')

    def handle_disconnect(self):
        print('You disconnect from the server')

    def start(self):
        try:
            self.socket.connect(os.getenv('SOCKET_URL'))
            self.socket.wait()
        except Exception as e:
            print('> Error connecting: ', e)
    
    def handle_message(self, data):
        # Data's structure { "data": {Message content}, "channels": [{"streamerName": Name, "jobId": id, "lan": Language}], "caseId": caseId, "taskId": taskId}
        
        sha_data = pseudo_anonymize(data)
        streamer_name = sha_data['data']['streamer']
        msg_data = sha_data.get('data')
        hash_streamer_name = msg_data.get('streamer', 'unknown_streamer')
        channels = data.get('channels')
        caseId = data.get('caseId')
        taskId = data.get('taskId')

        for streamer_data in channels: 
            if streamer_data.get('streamerName') == streamer_name:
                jobId = streamer_data.get('jobId')

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
            "lang": msg_data.get("lang"),
            "attributes": {
                "authorName": msg_data['username']
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
            document_response, document_response_status = make_request(f"{os.getenv('NEO4J_URL')}/documents/SocialMedia", None, None, document_data, "POST")
            entity_response, entity_response_status  = make_request(f"{os.getenv('NEO4J_URL')}/entities", None, None, entity_data, "POST")
            if document_response_status != 201 or entity_response_status != 201:
                return
            
            docId = document_response['data']['id']
            entityId = entity_response['data']['id']
            relationship_data = {
                "sourceNodeId": docId,
                "targetNodeId": entityId,
                "type": "hasAuthor"
            }
            
            _, _ = make_request(f"{os.getenv('NEO4J_URL')}/relationships", None, None, relationship_data, "POST")

            self.send_message_to_kafka(streamer_name, caseId, taskId, jobId, docId)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def generate_message_tas_results(self, sentUtc, streamer, caseId, taskId, jobId, documentId):
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
        topic, message = self.generate_message_tas_results(
            datetime.datetime.utcnow().isoformat().split(".")[0] + 'Z',
            streamer_name,
            caseId, 
            taskId, 
            jobId, 
            docId)
        self.producer.send_message(topic, message)

def make_request(url, params=None, headers=None, data=None, method="GET"):
    try:
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
            'data': response.json()
        }
        return response_data, response.status_code
    
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
        print(f"The error data is {error_data} with status {status_code}")
        return error_data, status_code
    
    except ValueError as e:
        error_data = {
            'status': 'Error',
            'message': 'JSON Decoding Error'
            }
        return error_data, 500
    
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

if __name__ == '__main__':
    socket_client = SocketClient()
    socket_client.start()
