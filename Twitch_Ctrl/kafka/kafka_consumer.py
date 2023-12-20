from confluent_kafka import Consumer, KafkaError
import json

class MessageConsumer:
    def __init__(self, bootstrap_servers, group_id):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })

    def consume_messages(self, topic):
        self.consumer.subscribe([topic])

        try:
            while True:
                msg = self.consumer.poll(1.0)

                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print('Error: {}'.format(msg.error()))
                        break

                # Parse the JSON message
                received_message = json.loads(msg.value().decode('utf-8'))

                # Process the received message as needed
                print('Received message: {}'.format(received_message))

        except KeyboardInterrupt:
            pass
        finally:
            self.consumer.close()

# Example usage:
bootstrap_servers = 'localhost:9092'
topic = 'test_topic'
consumer = MessageConsumer(bootstrap_servers, 'my_group')
consumer.consume_messages(topic)
