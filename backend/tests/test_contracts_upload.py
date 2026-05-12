from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_contract_upload_queues_background(monkeypatch: pytest.MonkeyPatch, client: AsyncClient) -> None:
    async def _noop_pipeline(document_id, actor_id):  # noqa: ANN001
        return None

    monkeypatch.setattr(
        "app.api.v1.contracts.run_contract_pipeline",
        _noop_pipeline,
    )

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "uploader@example.com",
            "password": "supersecret123",
            "role": "legal_reviewer",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("sample.txt", b"hello world", "text/plain")}
    resp = await client.post("/api/v1/contracts/upload", headers=headers, files=files)
    assert resp.status_code == 202, resp.text
    payload = resp.json()
    assert "document_id" in payload


@pytest.mark.asyncio
async def test_contract_upload_accepts_jpeg_scan(
    monkeypatch: pytest.MonkeyPatch,
    client: AsyncClient,
) -> None:
    async def _noop_pipeline(document_id, actor_id):  # noqa: ANN001
        return None

    monkeypatch.setattr(
        "app.api.v1.contracts.run_contract_pipeline",
        _noop_pipeline,
    )

    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "uploader2@example.com",
            "password": "supersecret123",
            "role": "legal_reviewer",
        },
    )
    assert reg.status_code == 201
    token = reg.json()["tokens"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    jpeg_minimal = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    files = {"file": ("scan.jpg", jpeg_minimal, "image/jpeg")}
    resp = await client.post("/api/v1/contracts/upload", headers=headers, files=files)
    assert resp.status_code == 202, resp.text
    assert "document_id" in resp.json()
