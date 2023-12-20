from confluent_kafka import Producer
import json

class MessageProducer:
    def __init__(self, bootstrap_servers):
        self.bootstrap_servers = bootstrap_servers
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})

    def delivery_report(self, err, msg):
        if err is not None:
            print('Message delivery failed: {}'.format(err))
        else:
            print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

    def send_message(self, topic, message_data):
        message = {
            'type': 'your_message_type',
            'data': message_data
        }

        # Convert the message to JSON
        message_json = json.dumps(message)

        # Send the JSON message to Kafka
        self.producer.produce(topic, value=message_json, callback=self.delivery_report)
        self.producer.flush()

    def close_producer(self):
        self.producer.flush()

# Example usage:
producer = MessageProducer('your_kafka_bootstrap_servers')
message_data = {'key1': 'value1', 'key2': 'value2'}
producer.send_message('your_kafka_topic', message_data)
producer.close_producer()
