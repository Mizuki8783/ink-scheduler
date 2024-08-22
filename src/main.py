import os
import time
from dotenv import load_dotenv
load_dotenv()

from flask import request, jsonify
from functions import flask_app, get_response, instagram_bot
from util import *


@flask_app.route('/handle_appointment', methods=['POST'])
def new_appointment():
    data = request.json  # request stores the data posted through API (i.e. thread_id and message)
    history = data.get('history', "")  #figure out the way to send a list of messages over API
    user_query = data.get('message', "")
    ig_page = data.get('ig_page', "")

    task = get_response.apply_async(args=[user_query, history, ig_page])

    return jsonify({"task_id": task.id})

@flask_app.route('/status/<task_id>', methods=['GET'])
def check_status(task_id):
    # Import the add task from tasks.py
    start = time.time()
    response = {'result': 'Pending'}

    while (time.time() - start < 8) and response['result'] == 'Pending':

        task = get_response.AsyncResult(task_id)
        if task.state == 'PENDING':
            response = {'result': 'Pending'}
        elif task.state == 'SUCCESS':
            response = {'result': task.result}
        else: # Handle failure case
            response = {
                'result': "すみません、システム内部でエラーが発生しました。直接アカウントにお問い合わせください。",
                'exception': str(task.info)# Exception information
            }
    return jsonify(response)

@flask_app.route('/webhook', methods=['POST']) # default route
def webhook():
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

@flask_app.route('/mark_unread', methods=['POST'])
def unread_message():
    data = request.json  # request stores the data posted through API (i.e. thread_id and message)
    username = data.get('ig_page', "")  #figure out the way to send a list of messages over API

    user_id =instagram_bot.user_id_from_username(username)
    thread = instagram_bot.direct_thread_by_participants([user_id])
    r = instagram_bot.direct_thread_mark_unread(int(thread["thread"]["thread_id"]))

    return "Done"

if __name__ == '__main__':
    calendar_start_sync()
    flask_app.run(port=os.getenv("PORT", default=5000), debug=True) #port variable is given by railway
