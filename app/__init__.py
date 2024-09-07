from flask import Flask
from config import Config
from celery import Celery, Task

def create_celery(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app


def create_flask():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.webhook import bp as webhook_bp
    app.register_blueprint(webhook_bp, url_prefix='/webhook')

    # from app.auth import bp as auth_bp
    # app.register_blueprint(auth_bp)

    create_celery(app)

    return app
