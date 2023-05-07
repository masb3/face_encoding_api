import os
import pathlib
from typing import Union
from uuid import UUID

import aiofiles
from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel

from face_encoding_api.app import db
from face_encoding_api.app.constants import FACE_ENCODING_STATUS_CREATED
from face_encoding_api.app.worker import face_encoding_task


class FaceEncodingResp(BaseModel):
    id: UUID
    status: str
    face_encoding: list[float] = []


class StatsResp(BaseModel):
    total: int = 0
    created: int = 0
    completed: int = 0
    failed: int = 0


app = FastAPI()


@app.on_event("startup")
async def startup():
    await db.database.connect()


@app.on_event("shutdown")
async def shutdown():
    await db.database.disconnect()


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile) -> Union[FaceEncodingResp, dict]:
    contents = await file.read()

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail=f"Unexpected content-type '{file.content_type}'"
        )
    if file.size > 10 ** 7:
        raise HTTPException(status_code=400, detail="File size limit 10MB")

    item_id = await db.create_face_encoding()

    file_extension = pathlib.PurePath(file.filename).suffix
    path_filename = f"{os.getcwd()}/files/{str(item_id)}{file_extension}"
    os.makedirs(
        os.path.dirname(path_filename), exist_ok=True
    )  # create folder if not exists
    async with aiofiles.open(path_filename, "wb") as f:
        await f.write(contents)
        face_encoding_task.apply_async(
            kwargs={"item_id": str(item_id), "path_filename": path_filename}
        )

    await file.close()

    return FaceEncodingResp(
        id=item_id,
        status=FACE_ENCODING_STATUS_CREATED,
        face_encoding=[],
    )


@app.get("/face_encoding/{item_id}")
async def face_encoding(item_id: UUID) -> FaceEncodingResp:
    result = await db.get_face_encoding(item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return FaceEncodingResp(**result)


@app.get("/stats/")
async def stats() -> StatsResp:
    result = await db.get_stats()
    return StatsResp(**result)
