from app import create_flask
from app.tasks import get_response
# from app.utils.util import calendar_start_sync
# calendar_start_sync() # I dont think I should start the sync here. I gotta start it rather when a user sign up

app = create_flask()
celery = app.extensions["celery"]

@app.shell_context_processor
def make_shell_context():
    return {'app': app}

print(f"-----------------{__name__}-----------------")
