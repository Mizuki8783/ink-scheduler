from app.webhook import bp
from flask import request
import time
from app.utils.util import *

@bp.route('/calendar_update', methods=['POST']) # default route
def calendar_update():
    headers = request.headers

    if headers["X-Goog-Resource-State"] == "exists":
        events_result = calendar_get_diff()
        if events_result["items"] == []:
            return 'No events to process'
        if len(events_result["items"]) != 1:
            print('Error: multiple events to process')
            return 'Error: multiple events to process'

        event = events_result["items"][0]
        time.sleep(7) # If the event was just created, airtable needs time to retrieve and updated the event_id
        records = airtable_get(event_id = event["id"])
        if event["status"] == "cancelled":
            if len(records) == 0:
                print("record already deleted")
                return "record already deleted"
            if len(records) == 1:
                record_id = records[0]["id"]
                airtable_delete(record_id)
                print("deleted a record in airtable")
                return 'webhook success'
            else:
                print("Error: multiple records to process")
                return 'webhook fail, needs to be fixed'

        if event["status"] == "confirmed" and '_' in event.get('summary',''):
            start_time = event["start"]["dateTime"]
            end_time = event["end"]["dateTime"]
            elements_dict = breakup_elements(event['summary'], event['description'])

            if len(records) == 0:
                print("insering a record in airtable")
                res = airtable_upsert(**elements_dict, start_time=start_time, end_time=end_time, event_id=event["id"], webhook_flg="1")
            if len(records) == 1:
                record_id = records[0]["id"]
                print("updating a record in airtable")
                res = airtable_upsert(**elements_dict, start_time=start_time, end_time=end_time, record_id=record_id, webhook_flg="1")
                res = airtable_upsert(record_id=record_id, webhook_flg="0") #Set the webhook_flg to 0
            else:
                print("Error: multiple records to process")
                return 'webhook fail, needs to be fixed'


            if res.status_code == 200:
                      print("Webhook was called successfully!")
            else:
                print("Webhook Error: " + res.text)

    else:
        print("----------Webhook Resource State: " + headers["X-Goog-Resource-State"] + "-------------")

    return "webhook done"

print(f"-----------------{__name__}-----------------")
