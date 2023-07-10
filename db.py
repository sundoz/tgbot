from pymongo import MongoClient

def create_client(MONGO):
    client = MongoClient(host=MONGO, 
                        port=27017)
    db = client['delegations']
    wishs_collection = db['wishs_collection']
    return wishs_collection


    