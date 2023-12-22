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
        # data's structure { "data": {Message info}, "channels": {"streamer name": "jobId"}, "caseId": caseId, "taskId": taskId}
        modified_message = data.get('data')
        channels = data.get('channels')
        caseId = data.get('caseId')
        taskId = data.get('taskId')
        streamer_name = modified_message.get('streamer', 'unknown_streamer')

        document_data = {
            "jobId": channels.get(streamer_name),
            "domainId": f"twitch:comment:{channels.get(streamer_name)}",
            "title": modified_message.get("message"),
            "content": modified_message.get("message"),
            "raw": "{}",
            "source": "twitch",
            "type": "twitch:comment",
            "publishedAt": modified_message.get("created_at"),
            "discoveredAt": modified_message.get("created_at"),
            "lang": ""
        }
        entity_data = {
            "domainId":f"twitch:profile:{modified_message.get("username")}",
            "title":modified_message.get("username"),
            "name":modified_message.get("username"),
            "source":"twitch",
            "type":"twitch:profile",
            "discoveredAt": modified_message.get("created_at")
        }
        print(f"Document data (before post request)> {document_data}")

        try:
            create_document_response, document_response = make_request(f"{os.getenv('NEO4J_URL')}/documents/SocialMedia", None, None, document_data, "POST")
            create_entity_response, entity_response  = make_request(f"{os.getenv('NEO4J_URL')}/entities", None, None, entity_data, "POST")

            print("!!!POST requests successful!!")
            print(f'>the created document is {create_document_response}, and response {document_response}')
            print(f'>the created entity is {create_entity_response}, and response {entity_response}')
            print(f">Now we will send the meesage to kafka\n")
            topic, message = self.generate_message_tas_results(
                datetime.datetime.utcnow().isoformat().split(".")[0] + 'Z',
                streamer_name,
                caseId, 
                taskId, 
                channels.get(streamer_name), 
                create_document_response['data']['id'])
            self.producer.send_message(topic, message)
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
    
if __name__ == '__main__':
    socket_client = SocketClient()
    socket_client.start()
