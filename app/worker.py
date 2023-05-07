import face_recognition
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from face_encoding_api.app.constants import (
    FACE_ENCODING_STATUS_CREATED,
    FACE_ENCODING_STATUS_COMPLETED,
    FACE_ENCODING_STATUS_FAILED,
)
from face_encoding_api.app.db import psycopg2_conn
from face_encoding_api.settings import settings


app = Celery(__name__)
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
# app.conf.task_ignore_result = True

conn = None


@worker_process_init.connect
def init_worker(**kwargs):
    global conn
    conn = psycopg2_conn()


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    global conn
    if conn:
        conn.close()


@app.task(name="face_encoding_task")
def face_encoding_task(item_id: str, path_filename: str):
    # Update only if id exists and current state 'created'
    query = """
                UPDATE face_encodings
                SET status = %(new_status)s, face_encoding = %(face_encoding)s 
                WHERE id = %(item_id)s AND status = %(cur_status)s;
            """

    with conn.cursor() as cur:
        failed = False
        face_encodings = None
        try:
            img = face_recognition.load_image_file(path_filename)
            face_encodings = face_recognition.face_encodings(img)
        except FileNotFoundError:
            failed = True
        finally:
            cur.execute(
                query,
                {
                    "item_id": item_id,
                    "cur_status": FACE_ENCODING_STATUS_CREATED,
                    "new_status": FACE_ENCODING_STATUS_COMPLETED
                    if not failed
                    else FACE_ENCODING_STATUS_FAILED,
                    "face_encoding": face_encodings[0].tolist()
                    if face_encodings and not failed
                    else None,
                },
            )
            conn.commit()
