import pymongo
from bson import json_util
import json
from utilities.utils import db_config

clientName, db_name, collection_name = db_config()
client = pymongo.MongoClient(clientName)
db = client[db_name]
collection = db[collection_name]

def multiple_update_db(games, filterName):
    bulk_operations = []
    print(f"the length of the games {len(games['data'])}")
    for game in games["data"]:
        filter = {"id": game[filterName]}
        update = {"$set": game}
        bulk_operations.append(pymongo.UpdateOne(filter, update, upsert=True))

    result = collection.bulk_write(bulk_operations)
    
    print(f"Number of upserted count is: {result.upserted_count}")
    print(f"Number of modified count is: {result.modified_count}")

def update_db(game, filterName):
    filter = {"id": game[filterName]}
    update = {"$set": game}
    collection.find_one_and_update(filter, update, upsert=True)

    count = collection.count_documents({})
    print(f"Number of documents in the collection: {count}")
    client.close()

def create_text_index():
    # Create a "text" index on the desired field
    collection.create_index([("name", "text")], default_language="english")
    print("Index created successfully")

def get_exact_match(query):
    result = collection.find_one(query, projection={"_id": 0})
    return {"data": [result]} 

def get_text_index(keyword, limit):
    result = collection.find(
        {"$text": {"$search": keyword}},
        {"score": {"$meta": "textScore"}, "_id": 0}
    ).sort([("score", {"$meta": "textScore"})]).limit(limit)
    
    return {"data": list(result)} 