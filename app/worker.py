from urllib.parse import urlparse

import face_recognition
import psycopg2
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from face_encoding_api.app.constants import (
    FACE_ENCODING_STATUS_CREATED,
    FACE_ENCODING_STATUS_COMPLETED,
    FACE_ENCODING_STATUS_FAILED,
)
from face_encoding_api.settings import settings


app = Celery(__name__)
app.conf.broker_url = settings.CELERY_BROKER_URL
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
# app.conf.task_ignore_result = True

conn = None


@worker_process_init.connect
def init_worker(**kwargs):
    global conn
    db_url = urlparse(settings.DATABASE_URL)
    conn = psycopg2.connect(
        dbname=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        host=db_url.hostname,
        port=db_url.port,
    )


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    global conn
    if conn:
        conn.close()


@app.task(name="face_encoding_task")
def face_encoding_task(item_id: str, path_filename: str):
    query_validate_exists = """
                        SELECT EXISTS
                        (SELECT 1 
                        FROM face_encodings 
                        WHERE id = %(item_id)s AND status = %(status)s);
                    """
    query_insert_encoding = """
                    UPDATE face_encodings
                    SET status = %(status)s, face_encoding = %(face_encoding)s 
                    WHERE id = %(item_id)s;
                    """

    with conn.cursor() as cur:
        cur.execute(
            query_validate_exists,
            {"item_id": item_id, "status": FACE_ENCODING_STATUS_CREATED},
        )
        if not cur.fetchone()[0]:
            return
        try:
            img = face_recognition.load_image_file(path_filename)
            face_encodings = face_recognition.face_encodings(img)
            cur.execute(
                query_insert_encoding,
                {
                    "item_id": item_id,
                    "status": FACE_ENCODING_STATUS_COMPLETED,
                    "face_encoding": face_encodings[0].tolist()
                    if face_encodings
                    else None,
                },
            )
            conn.commit()
        except:  # FIXME: too broad
            cur.execute(
                query_insert_encoding,
                {"item_id": item_id, "status": FACE_ENCODING_STATUS_FAILED},
            )
            conn.commit()
