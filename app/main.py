import os

import face_recognition
import aiofiles
from typing import Union

from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

from face_encoding_api.app.worker import create_task

app = FastAPI()


class ImgEncoding(BaseModel):
    encoding: list[float] = []


@app.get("/")
async def root():
    create_task.apply_async(kwargs={"task_type": 1})
    return {"Hello!!!!"}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile) -> Union[ImgEncoding, dict]:
    try:
        contents = await file.read()
        path_filename = f"{os.getcwd()}/files/{file.filename}"
        os.makedirs(os.path.dirname(path_filename), exist_ok=True)  # create folder if not exists
        async with aiofiles.open(path_filename, "wb") as f:
            await f.write(contents)
            # TODO: rename file to uuid
            # TODO: save uuid to db
            # TODO: encoding move to celery
            img = face_recognition.load_image_file(f.name)
            img_encoding = face_recognition.face_encodings(img)
    except Exception:  # FIXME: too broad
        return {"message": "Error uploading the file"}
    finally:
        await file.close()

    return ImgEncoding(encoding=img_encoding[0].tolist())
