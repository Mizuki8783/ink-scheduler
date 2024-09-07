import requests
import json
import os
from datetime import datetime
import ast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from dotenv import load_dotenv
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

from pymongo import MongoClient
from cryptography.fernet import Fernet

ig_name = input("Enter your Instagram username: ")

#######Retrieving Google Calendar Credentials########
# Connect to the MongoDB server
client = MongoClient(os.getenv("MONGODB_URL"))
db = client['secrets']
collection = db['credentials']

g_api_cred = collection.find_one({"cred_name": "google_calendar"})

cipher_suite = Fernet(os.getenv("FERNET_KEY"))
for key in ["client_id", "client_secret", "project_id"]:
    g_api_cred["creds"]["web"][key] = cipher_suite.decrypt(g_api_cred["creds"]["web"][key].encode()).decode()

######Issuing Google Calendar Token########
flow = InstalledAppFlow.from_client_config(
    g_api_cred["creds"],
    SCOPES
    )
gc_client_creds = flow.run_local_server(port=8080, timeout=30)

token = json.loads(gc_client_creds.to_json())

#####Issuing Google Calendar Sync Token########
calendar_client = build("calendar", "v3", credentials=gc_client_creds)

request_args = {
    "calendarId": "primary",
    "showDeleted": True,
}
events_result = calendar_client.events().list(**request_args).execute()

while events_result.get("nextPageToken"):
    request_args["pageToken"] = events_result["nextPageToken"]
    events_result = calendar_client.events().list(**request_args).execute()

sync_token = {"nextSyncToken": events_result["nextSyncToken"]}

######Encrypting Google Calendar Tokens########
token["token"] = cipher_suite.encrypt(token["token"].encode()).decode()
token["refresh_token"] = cipher_suite.encrypt(token["refresh_token"].encode()).decode()
token["client_id"] = cipher_suite.encrypt(token["client_id"].encode()).decode()
token["client_secret"] = cipher_suite.encrypt(token["client_secret"].encode()).decode()

sync_token["nextSyncToken"] = cipher_suite.encrypt(sync_token["nextSyncToken"].encode()).decode()


######Storing Google Calendar Tokens########
document = {
    "user_id" : "1",
    "user_ig_name" : ig_name,
    "token" : token,
    "sync_token" : sync_token,
    "created_at": datetime.now(),
    "updated_at": datetime.now()
 }

collection = db['users']
collection.insert_one(document)

print("Setup completed")
