import os
import uuid

import pytest

from face_encoding_api.app import db
from face_encoding_api.app import worker
from face_encoding_api.app.constants import FACE_ENCODING_STATUS_CREATED


def test_create_upload_file(test_app, monkeypatch):
    item_id = uuid.UUID("dce15431-a672-4ef2-b94d-4fe2f16b482f")
    expected_resp = {
        "id": str(item_id),
        "status": FACE_ENCODING_STATUS_CREATED,
        "face_encoding": [],
    }

    async def mock_create_face_encoding():
        return item_id

    def mock_face_encoding_task(*args, **kwargs):
        return

    monkeypatch.setattr(db, "create_face_encoding", mock_create_face_encoding)
    monkeypatch.setattr(worker.app, "send_task", mock_face_encoding_task)
    with open(f"{os.getcwd()}/face_encoding_api/app/tests/files/people.jpg", "rb") as f:
        resp = test_app.post(
            "/uploadfile/", files={"file": ("people.jpg", f, "image/jpeg")}
        )

    assert resp.status_code == 201
    assert resp.json() == expected_resp


def test_create_upload_file_unexpected_content_type(test_app, monkeypatch):
    item_id = uuid.UUID("dce15431-a672-4ef2-b94d-4fe2f16b482f")

    async def mock_create_face_encoding():
        return item_id

    def mock_face_encoding_task(*args, **kwargs):
        return

    monkeypatch.setattr(db, "create_face_encoding", mock_create_face_encoding)
    monkeypatch.setattr(worker.app, "send_task", mock_face_encoding_task)
    with open(f"{os.getcwd()}/face_encoding_api/app/tests/files/people.jpg", "rb") as f:
        resp = test_app.post(
            "/uploadfile/", files={"file": ("people.jpg", f, "application/jpeg")}
        )

    assert resp.status_code == 400
    assert resp.json() == {"detail": f"Unexpected content-type 'application/jpeg'"}


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete", "options"])
def test_create_upload_file_api_method_not_allowed(test_app, method):
    resp = getattr(test_app, method)(f"/uploadfile/")

    assert resp.status_code == 405


def test_face_encoding(test_app, monkeypatch):
    item_id = "dce15431-a672-4ef2-b94d-4fe2f16b482f"
    expected_resp = {
        "id": item_id,
        "status": "completed",
        "face_encoding": [
            -0.1101314127445221,
            0.1322958916425705,
            0.04110884293913841,
            -0.04484809190034866,
        ],
    }

    async def mock_get_face_encoding(item_id):
        return expected_resp

    monkeypatch.setattr(db, "get_face_encoding", mock_get_face_encoding)
    resp = test_app.get(f"/face_encoding/{item_id}")

    assert resp.status_code == 200
    assert resp.json() == expected_resp


def test_face_encoding_invalid_id(test_app, monkeypatch):
    item_id = "dce15431-a672-4ef2-b94d-4fe2f16b482f"

    async def mock_get_face_encoding(item_id):
        return None

    monkeypatch.setattr(db, "get_face_encoding", mock_get_face_encoding)
    resp = test_app.get(f"/face_encoding/{item_id}")

    assert resp.status_code == 404
    assert resp.json() == {"detail": "Item not found"}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete", "options"])
def test_face_encoding_api_method_not_allowed(test_app, method):
    item_id = "dce15431-a672-4ef2-b94d-4fe2f16b482f"
    resp = getattr(test_app, method)(f"/face_encoding/{item_id}")

    assert resp.status_code == 405


@pytest.mark.parametrize("method", ["get", "options", "post", "put", "patch", "delete"])
def test_face_encoding_api_not_found(test_app, method):
    resp = getattr(test_app, method)(f"/face_encoding/")

    assert resp.status_code == 404


def test_stats(test_app, monkeypatch):
    expected_resp = {"total": 8, "created": 0, "completed": 7, "failed": 1}

    async def mock_get_stats():
        return expected_resp

    monkeypatch.setattr(db, "get_stats", mock_get_stats)
    resp = test_app.get("/stats")

    assert resp.status_code == 200
    assert resp.json() == expected_resp


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete", "options"])
def test_stats_api_method_not_allowed(test_app, method):
    resp = getattr(test_app, method)("/stats")

    assert resp.status_code == 405
