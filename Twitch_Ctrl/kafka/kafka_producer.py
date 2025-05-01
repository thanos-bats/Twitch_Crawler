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
        """Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush()."""
        if err is not None:
            print(f'Message delivery failed: {err}')
            print(f'Failed message details: Topic={msg.topic()}, Partition={msg.partition()}, Offset={msg.offset()}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}')

    def send_message(self, topic, message_data):
        try:
            message_json = json.dumps(message_data)
            print(f"\nSending message to topic {topic}: {message_json}")
            
            # Produce the message
            self.producer.produce(topic, value=message_json, callback=self.delivery_report)
            
            # Wait for any outstanding messages to be delivered and delivery reports to be received
            self.producer.flush()
            
        except Exception as e:
            print(f"Error producing message to Kafka: {str(e)}")
            print(f"Topic: {topic}")
            print(f"Message data: {message_data}")
            raise  # Re-raise the exception to allow caller to handle it

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
