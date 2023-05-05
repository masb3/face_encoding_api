import os
import pathlib

from typing import Union

import aiofiles
import databases
import face_recognition

from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

from face_encoding_api.settings import settings
from face_encoding_api.app.worker import create_task


database = databases.Database(settings.DATABASE_URL)


class ImgEncoding(BaseModel):
    encoding: list[float] = []


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


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile) -> Union[ImgEncoding, dict]:
    try:
        contents = await file.read()

        query = "INSERT INTO face_encodings (status) VALUES ('created') RETURNING id;"
        record_id = await database.execute(query)

        file_name = str(record_id)
        file_extension = pathlib.PurePath(file.filename).suffix
        path_filename = f"{os.getcwd()}/files/{file_name}{file_extension}"
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

    return ImgEncoding(encoding=img_encoding[0].tolist())
