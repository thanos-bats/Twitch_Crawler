
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException
from dotenv import load_dotenv
from kafka_producer import MessageProducer
import os

load_dotenv()
def topic_exists(admin_client, topic_name):
    """Check if a Kafka topic exists."""
    topic_metadata = admin_client.list_topics(timeout=10)
    return topic_name in topic_metadata.topics

def create_topic(admin_client, topic_name, num_partitions=1, replication_factor=1):
    """Create a Kafka topic."""
    new_topic = NewTopic(topic_name, num_partitions=num_partitions, replication_factor=replication_factor)
    try:
        admin_client.create_topics([new_topic])
        print(f"Topic {topic_name} created")
    except KafkaException as e:
        print(f"Failed to create topic {topic_name}: {e}")
        return False
    return True


def main():
    # For testing purposes
    bootstrap_servers = os.getenv('BOOTSTRAP_SERVERS')
    topic_name = os.getenv('TOPIC_MESSAGE_DONE')
    print('Bootstrap Servers:', bootstrap_servers)
    print('Topic:', topic_name)
    # Create Kafka Admin Client
    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    # Check if topic exists and create it if it doesn't
    if not topic_exists(admin_client, topic_name):
        print(f"Topic {topic_name} does not exist, creating it.")
        create_topic(admin_client, topic_name)
    else:
        print(f"Topic {topic_name} already exists.")

    # # Instantiate the MessageProducer
    producer = MessageProducer(bootstrap_servers)


    # Send a message
    message_data = {'key1': 'value1', 'key2': 'value2'}
    producer.send_message(topic_name, message_data)

    # Close the producer
    producer.close_producer()


if __name__ == '__main__':
    main()
