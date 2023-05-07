import face_recognition
import psycopg2
from celery import Celery

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

conn = psycopg2.connect(
    dbname=settings.POSTGRES_DB,
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
)


@app.task(name="create_task")
def create_task(item_id: str, path_filename: str):
    query_validate_exists = """
                        SELECT EXISTS
                        (SELECT 1 
                        FROM face_encodings 
                        WHERE id = %(item_id)s AND status = %(status)s);
                    """
    query_insert_encoding = """
                    UPDATE face_encodings
                    SET status = %(status)s 
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
                {"item_id": item_id, "status": FACE_ENCODING_STATUS_COMPLETED},
            )
            # TODO: face_encodings[0].tolist() if face_encodings else []
            conn.commit()
        except:  # FIXME: too broad
            cur.execute(
                query_insert_encoding,
                {"item_id": item_id, "status": FACE_ENCODING_STATUS_FAILED},
            )
            conn.commit()
