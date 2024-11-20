import os

class Config:
    SECRET_KEY = os.environ.get("FERNET_KEY") or "hard to guess string"
    CELERY = {
        "broker_url": os.environ.get("REDIS_URL") or "redis://localhost:6379/0",
        "result_backend": os.environ.get("REDIS_URL") or "redis://localhost:6379/0"
    }


print(f"-----------------{__name__}-----------------")
