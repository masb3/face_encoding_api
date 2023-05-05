import os
import pathlib
from typing import Union
from uuid import UUID

import aiofiles
import databases
import face_recognition
from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel

from face_encoding_api.app.constants import FACE_ENCODING_STATUS_CREATED
from face_encoding_api.app.worker import create_task
from face_encoding_api.settings import settings

database = databases.Database(settings.DATABASE_URL)


class FaceEncodingResp(BaseModel):
    id: UUID
    face_encoding: list[float] = []
    status: str


class StatsResp(BaseModel):
    total: int = 0
    created: int = 0
    in_progress: int = 0  # TODO: remove as obsolete
    completed: int = 0
    failed: int = 0


app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/")
async def root():
    create_task.apply_async(kwargs={"task_type": 1})
    return {"Hello!!!!"}


@app.get("/face_encoding/{item_id}")
async def get_face_encoding(item_id: UUID) -> FaceEncodingResp:
    query = """
                SELECT COALESCE(face_encoding, ARRAY[]::FLOAT[]) as face_encoding, status
                FROM face_encodings
                WHERE id = :item_id;
            """
    result = await database.fetch_one(query, {"item_id": item_id})
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return FaceEncodingResp(
        id=item_id,
        face_encoding=result._mapping["face_encoding"],
        status=result._mapping["status"],
    )


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile) -> Union[FaceEncodingResp, dict]:
    try:
        contents = await file.read()

        query = f"INSERT INTO face_encodings (status) VALUES ('{FACE_ENCODING_STATUS_CREATED}') RETURNING id;"
        record_id = await database.execute(query)

        file_extension = pathlib.PurePath(file.filename).suffix
        path_filename = f"{os.getcwd()}/files/{str(record_id)}{file_extension}"
        os.makedirs(
            os.path.dirname(path_filename), exist_ok=True
        )  # create folder if not exists
        async with aiofiles.open(path_filename, "wb") as f:
            await f.write(contents)
            # TODO: encoding move to celery
            img = face_recognition.load_image_file(f.name)
            img_encoding = face_recognition.face_encodings(img)
    except Exception:  # FIXME: too broad
        return {"message": "Error uploading the file"}
    finally:
        await file.close()

    return FaceEncodingResp(
        id=record_id,
        face_encoding=img_encoding[0].tolist(),
        status=FACE_ENCODING_STATUS_CREATED,
    )


@app.get("/stats/")
async def get_stats() -> StatsResp:
    query = """
                SELECT 'total' AS status, COUNT(*) AS count 
                FROM face_encodings 
                UNION 
                SELECT status, COUNT(*) 
                FROM face_encodings 
                GROUP BY status;
            """
    result = await database.fetch_all(query)
    return StatsResp(**{r._mapping["status"]: r._mapping["count"] for r in result})
