from confluent_kafka import Producer
import json
import os
from dotenv import load_dotenv
load_dotenv()

class ProducerHandler:
    def __init__(self, bootstrap_servers=None):
        if bootstrap_servers is None:
            self.bootstrap_servers = os.getenv('BOOTSTRAP_SERVERS')
        else:
            self.bootstrap_servers = bootstrap_servers

        print(f'Producer Configuration: {self.bootstrap_servers}')
        conf = {'bootstrap.servers': self.bootstrap_servers}
        self.producer = Producer(conf)

    def delivery_report(self, err, msg):
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    def send_message(self, topic, message_data):

        message_json = json.dumps(message_data)
        print(f"\nThe message: {message_json}")
        self.producer.produce(topic, value=message_json, callback=self.delivery_report)
        self.producer.flush()

    def close(self):
        if self.producer is not None:
            # Flush all outstanding messages before closing the producer
            self.producer.flush()

# Example usage:
# bootstrap_servers = os.getenv('BOOTSTRAP_SERVERS')
# topic = os.getenv('TOPIC_MESSAGE_DONE')

# print('Bootstrap Servers:', bootstrap_servers)
# print('Topic:', topic)

# # Instantiate the MessageProducer
# producer = ProducerHandler(bootstrap_servers)


# # Send a message
# message_data = {'key1': 'value1', 'key2': 'value2'}
# producer.send_message(topic, message_data)

# # Close the producer
# producer.close()
