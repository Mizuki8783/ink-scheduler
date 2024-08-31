import os
from datetime import datetime

from util import calender_client
from pymongo import MongoClient

from dotenv import load_dotenv
load_dotenv()

WEB_HOOK_URL = os.getenv("WEB_HOOK_URL")
ig_name = input("Enter your Instagram username: ")

# Global variables to store watch information
request_body = {
    'id': 'calendar_watch',
    'type': 'web_hook',
    'address': WEB_HOOK_URL,
    "params":{
        'ttl': 2592000 #30 days
        }
}
response = calender_client.events().watch(calendarId="primary", body=request_body).execute()

expiration_time = int(response['expiration']) / 1000  # Convert to seconds
response["expiration"] = datetime.fromtimestamp(expiration_time).strftime('%Y-%m-%d %H:%M:%S')

document = {
            "user_ig_name": ig_name,
            "watch_instance": response
            }

# Connect to the MongoDB server & Insert a record
client = MongoClient(os.getenv("MONGODB_URL"))
db = client['secrets']
collection = db['google_calender']
collection.insert_one(document)
