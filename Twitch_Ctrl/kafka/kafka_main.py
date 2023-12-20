
from kafka_consumer import MessageConsumer
from kafka_producer import MessageProducer
import time

def main():
    # For testing purposes
    bootstrap_servers = 'localhost:9092'
    topic = 'test_topic'

    producer = MessageProducer(bootstrap_servers)
    consumer = MessageConsumer(bootstrap_servers, 'my_group')

    # Sending a message
    message = {'key': 'value'}
    producer.send_message(topic, message)
    consumer.consume_messages(topic)


if __name__ == '__main__':
    main()
