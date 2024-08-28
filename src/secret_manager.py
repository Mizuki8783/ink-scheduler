import os
from dotenv import find_dotenv, load_dotenv
from pymongo import MongoClient
from cryptography.fernet import Fernet
from datetime import datetime

env_path = find_dotenv(usecwd=True)
load_dotenv()

# Connect to the MongoDB server
client = MongoClient(os.getenv("MONGODB_URL"))
db = client['secrets']
collection = db['users']

#Initialize Fernet
cipher_suite = Fernet(os.getenv("FERNET_KEY"))

def decrypte_secret(secret_name, secret):
    if secret_name == "token":
        keys_to_decrypt = ["token","refresh_token","client_id","client_secret"]
    elif secret_name == "sync_token":
        keys_to_decrypt = ["nextSyncToken"]
    elif secret_name == "user_ig_password":
        return  cipher_suite.decrypt(secret.encode()).decode()

    for key in keys_to_decrypt:
        secret[key] = cipher_suite.decrypt(secret[key].encode()).decode()

    return secret

def encrypte_secret(secret_name, secret):
    if secret_name == "token":
        keys_to_decrypt = ["token","refresh_token","client_id","client_secret"]
    elif secret_name == "sync_token":
        keys_to_decrypt = ["nextSyncToken"]
    elif secret_name == "user_ig_password":
        return  cipher_suite.encrypt(secret.encode()).decode()

    for key in keys_to_decrypt:
        secret[key] = cipher_suite.encrypt(secret[key].encode()).decode()

    return secret

def get_secret(ig_name,secret_name):
    _filter = {"user_ig_name": ig_name}
    retrieved_document = collection.find_one(_filter)

    encrypted_secret = retrieved_document[secret_name]
    decrypted_secret = decrypte_secret(secret_name, encrypted_secret)

    return decrypted_secret

def update_secret(ig_name,secret_name,secret):
    _filter = {"user_ig_name": ig_name}
    encrypted_secret = encrypte_secret(secret_name, secret)
    update_values = {"$set": {secret_name : encrypted_secret, "updated_at": datetime.now()}}

    result = collection.update_one(_filter, update_values)
    if result.modified_count == 1:
        print("Update successful")
    else:
        print("Update failed")

    return "Update successful"
