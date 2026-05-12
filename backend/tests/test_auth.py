from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_me_refresh(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "reviewer@example.com",
            "password": "supersecret123",
            "role": "legal_reviewer",
        },
    )
    assert resp.status_code == 201, resp.text
    bundle = resp.json()
    assert "tokens" in bundle
    headers = {"Authorization": f"Bearer {bundle['tokens']['access_token']}"}
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "reviewer@example.com"

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": bundle["tokens"]["refresh_token"]},
    )
    assert refresh.status_code == 200
    body = refresh.json()
    assert "access_token" in body
