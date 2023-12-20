# from bus_utilities.load_bus_credentials import LoadBusCredentials
from confluent_kafka.admin import AdminClient, NewTopic
#from shared import CONFIG

def list_topics(client):
    info = client.list_topics()
    tops = list(info.topics.keys())
    tops.sort()
    return tops

def cluster_info(client):
    return client.list_topics()

class AdminUtils:
    def __init__(self, bus_configuration=None, credentials_file=None):
        if bus_configuration is None:
            # bus_configuration = LoadBusCredentials().load_from_file(credentials_file)
            #self.__bus_configuration = CONFIG['kafka']
            print()
        else:
            self.__bus_configuration = bus_configuration

        self.__admin = AdminClient(self.__bus_configuration)

    def create_topic(self, topic_name, test_mode=True):
        new_topic = NewTopic(topic_name, num_partitions=1)
        # Change validate_only to False to actually create the topic
        return self.__admin.create_topics([new_topic], validate_only=test_mode)

if __name__ == '__main__':
    admin = AdminUtils(credentials_file="./../resources/bus_credentials.json")

    print(admin.create_topic(topic_name="Test_topic_X"))
