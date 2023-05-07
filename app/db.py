from urllib.parse import urlparse
from uuid import UUID

import databases
import psycopg2

from face_encoding_api.app.constants import FACE_ENCODING_STATUS_CREATED
from face_encoding_api.settings import settings


database = databases.Database(settings.DATABASE_URL)


def psycopg2_conn():
    db_url = urlparse(settings.DATABASE_URL)
    return psycopg2.connect(
        dbname=db_url.path[1:],
        user=db_url.username,
        password=db_url.password,
        host=db_url.hostname,
        port=db_url.port,
    )


async def create_face_encoding():
    query = "INSERT INTO face_encodings (status) VALUES (:status) RETURNING id;"
    return await database.execute(query, {"status": FACE_ENCODING_STATUS_CREATED})


async def get_face_encoding(item_id: UUID):
    query = """
                SELECT COALESCE(face_encoding, ARRAY[]::FLOAT[]) as face_encoding, status
                FROM face_encodings
                WHERE id = :item_id;
            """
    return await database.fetch_one(query, {"item_id": item_id})


async def get_stats():
    query = """
                SELECT 'total' AS status, COUNT(*) AS count 
                FROM face_encodings 
                UNION 
                SELECT status, COUNT(*) 
                FROM face_encodings 
                GROUP BY status;
            """
    return await database.fetch_all(query)
