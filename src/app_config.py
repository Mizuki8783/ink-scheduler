from celery import Celery, Task
from flask import Flask

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
            broker_url="redis://localhost:6379/0",
            result_backend="redis://localhost:6379/0"
        )
    )
    create_celery(app)
    return app
