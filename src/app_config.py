import os
from celery import Celery, Task
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_celery(app):
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.import_name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app

    return celery_app

def create_flask() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url=os.getenv("REDIS_URL"),
            result_backend=os.getenv("REDIS_URL")
        )
    )
    create_celery(app)
    return app
