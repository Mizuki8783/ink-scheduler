import os

class Config:
    SECRET_KEY = os.environ.get("FERNET_KEY") or "hard to guess string"
    CELERY = {
        "broker_url": os.environ.get("REDIS_URL"),
        "result_backend": os.environ.get("REDIS_URL")
    }


print(f"-----------------{__name__}-----------------")
