from flask import request, jsonify
from app.main import bp
from app.tasks import get_response
import time

@bp.route('/handle_appointment', methods=['POST'])
def new_appointment():
    data = request.json  # request stores the data posted through API (i.e. thread_id and message)
    history = data.get('history', "")  #figure out the way to send a list of messages over API
    user_query = data.get('message', "")
    ig_page = data.get('ig_page', "")

    task = get_response.apply_async(args=[user_query, history, ig_page])

    return jsonify({"task_id": task.id})

@bp.route('/status/<task_id>', methods=['GET'])
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

print(f"-----------------{__name__}-----------------")
