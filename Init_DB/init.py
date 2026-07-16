import pymongo
import json
import os
from dotenv import load_dotenv

def db_config():
    load_dotenv()
    db_uri = os.getenv("MONGO_DB")
    db_name = os.getenv("MONGO_DB_NAME")
    collection_name = os.getenv("MONGO_COLLECTION_NAME")
    print(db_uri, db_name, collection_name)
    # Check if the URI starts with 'mongodb://' or 'mongodb+srv://'
    if not db_uri.startswith("mongodb://") and not db_uri.startswith("mongodb+srv://"):
        raise ValueError("Invalid MongoDB URI. Must start with 'mongodb://' or 'mongodb+srv://'")

    return db_uri, db_name, collection_name

def load_dict_from_file(filename):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle file not found or JSON parsing error
        return {"data": []}

def insert_many(games):
    # Clear existing documents first so re-running this init (e.g. on every
    # `docker compose up`) does not create duplicate game entries.
    deleted = collection.delete_many({}).deleted_count
    if deleted:
        print(f"Cleared {deleted} existing documents before seeding.")
    result = collection.insert_many(games["data"])
    return result.inserted_ids

def create_text_index():
    # Create a "text" index on the desired field
    collection.create_index([("name", "text")], default_language="english")
    print("Index created successfully")

clientName, db_name, collection_name = db_config()
client = pymongo.MongoClient(clientName)
db = client[db_name]
collection = db[collection_name]

result = insert_many(load_dict_from_file('igdb_games.json'))
print(f'the result is {len(result)}')

create_text_index()