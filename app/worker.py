import time

from celery import Celery
from face_encoding_api.settings import settings


app = Celery(__name__)
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
# app.conf.task_ignore_result = True


@app.task(name="create_task")
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True