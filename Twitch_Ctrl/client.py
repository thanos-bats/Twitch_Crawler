import os
import json
import datetime
import requests

from socketio.client import Client
from dotenv import load_dotenv
from kafka.kafka_producer import MessageProducer

load_dotenv()

class SocketClient:
    def __init__(self):
        self.socket = Client()
        self.producer = MessageProducer(os.getenv('BOOTSTRAP_SERVERS'))

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
        # Data's structure { "data": {Message info}, "channels": [{"streamerName": Name, "jobId": id}], "caseId": caseId, "taskId": taskId}
        msg_data = data.get('data')
        streamer_name = msg_data.get('streamer', 'unknown_streamer')
        channels = data.get('channels')
        caseId = data.get('caseId')
        taskId = data.get('taskId')

        for streamer_data in channels: 
            if streamer_data.get('streamerName') == streamer_name:
                jobId = streamer_data.get('jobId')

        document_data = {
            "jobId": jobId,
            "domainId": f"twitch:comment:{streamer_name}",
            "title": None,
            "content": msg_data.get("message"),
            "raw": None,
            "source": "twitch",
            "type": "twitch:comment",
            "publishedAt": msg_data.get("created_at"),
            "discoveredAt": msg_data.get("created_at"),
            "lang": "und" # Maybe add the lang here
        }
        entity_data = {
            "domainId":f"twitch:profile:{msg_data.get("username")}",
            "title":None,
            "name":msg_data.get("username"),
            "source":"twitch",
            "type":"twitch:profile",
            "discoveredAt": msg_data.get("created_at")
        }

        try:
            document_response, document_response_status = make_request(f"{os.getenv('NEO4J_URL')}/documents/SocialMedia", None, None, document_data, "POST")
            entity_response, entity_response_status  = make_request(f"{os.getenv('NEO4J_URL')}/entities", None, None, entity_data, "POST")
            docId = document_response['data']['id']
            entityId = entity_response['data']['id']
            relationship_data = {
                "sourceNodeId": entityId,
                "targetNodeId": docId,
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
                "description": f"twitch chat logs on user's {streamer} stream",
                "data": [
                    {
                        "id": documentId,
                        "caseId": caseId,
                        "taskId": taskId,
                        "jobId": jobId
                    }
                ]
            }
        }

        return os.getenv("TOPIC_MESSAGE_DONE"), json.dumps(msg)

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

        return error_data, status_code
    
    except ValueError as e:
        error_data = {
            'status': 'Error',
            'message': 'JSON Decoding Error'
            }
        return error_data, 500
    
if __name__ == '__main__':
    socket_client = SocketClient()
    socket_client.start()
