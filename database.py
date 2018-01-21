from pymongo import MongoClient

def connect_db():
    db = MongoClient()['joinhider_bot']
    db.joined_user.create_index([('chat_id', 1), ('user_id', 1)])
    return db
