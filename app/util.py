import requests
import json
import os
import pytz
from datetime import datetime
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from secret_manager import get_secret, update_secret

from dotenv import load_dotenv
load_dotenv()

# #####Calender API Authentication########

# SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
# creds = None

# if os.path.exists("token.json"):
#   creds = Credentials.from_authorized_user_file("token.json", SCOPES)

# if not creds or not creds.valid:
#   if creds and creds.expired and creds.refresh_token:
#     creds.refresh(Request())
#   else:
#     flow = InstalledAppFlow.from_client_secrets_file(
#         "credentials.json", SCOPES
#     )
#     creds = flow.run_local_server(port=8080)
#   with open("token.json", "w") as token:
#     token.write(creds.to_json())
# #######################################

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
token = get_secret("tsm.automation", "token")
creds = Credentials.from_authorized_user_info(token, SCOPES)

if not creds:
    raise Exception("No token found")
elif not creds.valid and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    new_token = json.loads(creds.to_json())
    print("updating creds")
    res = update_secret("tsm.automation", "token", new_token)

calendar_client = build("calendar", "v3", credentials=creds)

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
base_id = "appEfKbQbUD5ECI7L"
table_name = "appointments"
headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def airtable_get(ig_page=None, start_time=None, event_id=None):
    if event_id is not None:
        filter_formula = f"AND({{event_id}}='{event_id}')"
    elif start_time is not None:
        filter_formula = f"AND({{ig_page}}='{ig_page}', {{start_time}}='{start_time}')"
    else:
        filter_formula = f"{{ig_page}}='{ig_page}'"

    url = f'https://api.airtable.com/v0/{base_id}/{table_name}?filterByFormula={requests.utils.quote(filter_formula)}'

    res = requests.get(url,headers=headers)
    records = res.json()['records']

    return records

def airtable_upsert(ig_page=None, name=None, start_time=None, end_time=None, design=None, size=None, placement=None, appointment_type=None, event_id=None, webhook_flg=None, record_id=None):
    fields = {k: v for k, v in locals().items() if v is not None and k != "record_id"}
    data = {
        'fields': {
            **fields
        }
    }

    if record_id == None and ig_page:
        url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
        res = requests.post(url,headers=headers,data=json.dumps(data))
    elif record_id:
        url = f'https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}'
        res = requests.patch(url, headers=headers, data=json.dumps(data))
    else:
        res = "airtable upsert failed. No record_id or ig_page"

    return res

def airtable_delete(record_id):
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}"
    res = requests.delete(url, headers=headers)

    return res

def calendar_start_sync():
    request_args = {
        "calendarId": "primary",
        "showDeleted": True,
    }
    events_result = calendar_client.events().list(**request_args).execute()

    while events_result.get("nextPageToken"):
        request_args["pageToken"] = events_result["nextPageToken"]
        events_result = calendar_client.events().list(**request_args).execute()

    update_secret("tsm.automation", "sync_token", {"nextSyncToken": events_result["nextSyncToken"]})
    print("Sync Success!!")

def calendar_get(start_time, end_time, q=None):
    request_args = {
        "calendarId": "primary",
        "timeMin": start_time,
        "timeMax": end_time,
        "singleEvents": True,
        "orderBy": "startTime"
    }
    if q is not None:
        request_args["q"] = q

    events_result = calendar_client.events().list(**request_args).execute()
    events = events_result.get("items", [])

    return events

def calendar_get_diff():
    sync_token = get_secret("tsm.automation", "sync_token")["nextSyncToken"]
    events_result = calendar_client.events().list(calendarId="primary",syncToken=sync_token).execute()

    if len(events_result["items"]) != 0:
        update_secret("tsm.automation", "sync_token", {"nextSyncToken": events_result["nextSyncToken"]})

    return events_result

def calendar_delete(event_id):
    request_args = {
        "calendarId": "primary",
        "eventId": event_id
    }

    events_result = calendar_client.events().delete(**request_args).execute()

    return events_result

def jst_to_utc(jst_time_str: str) -> str:
    jst_time = datetime.fromisoformat(jst_time_str)
    utc_time = jst_time.astimezone(pytz.utc)
    utc_time_str = utc_time.strftime('%Y-%m-%dT%H:%M:%S.000Z') #airflow only accepts UTC with three 0s for millisecond format when retrieving data

    return  utc_time_str

def utc_to_jst(utc_time_str: str) -> str:
    utc_time = datetime.fromisoformat(utc_time_str)
    jst_time = utc_time.astimezone(pytz.timezone("Asia/Tokyo"))
    jst_time_str = jst_time.isoformat(timespec="seconds")

    return jst_time_str


def breakup_elements(summary, description):
    def extract_pattern(pattern, text):
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    try:
        appointment_type, name, ig_page = summary.split('_')
    except:
        appointment_type, name, ig_page = ["不明", f"{datetime.now().isoformat(timespec="seconds")}", "不明"]

    return {
        'size': extract_pattern(r'サイズ：\s*(.*?)\s*配置：', description),
        'placement': extract_pattern(r'配置：\s*(.*?)\s*デザイン：', description),
        'design': extract_pattern(r'デザイン：\s*(.*)', description),
        'appointment_type': appointment_type,
        'name': name,
        'ig_page':ig_page
    }
