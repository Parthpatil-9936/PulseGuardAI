import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    resp = await client.post("/auth/login", json={"email": "alice@ward.icu", "password": "pass123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "doctor"
    assert data["user_id"] == "doc_1"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    resp = await client.post("/auth/login", json={"email": "alice@ward.icu", "password": "wrongpassword"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_rbac_denial_admin_endpoint(client: AsyncClient, auth_headers):
    # Nurse Carol attempts to access Admin-only /audit-logs
    headers = auth_headers("nurse_1", "nurse")
    resp = await client.get("/audit-logs", headers=headers)
    assert resp.status_code == 403
    assert "Action requires one of roles: admin" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_rbac_patient_assignment_enforcement(client: AsyncClient, auth_headers):
    # Dr. Alice is assigned to pat_1 -> should succeed
    headers_alice = auth_headers("doc_1", "doctor")
    resp_alice = await client.get("/patients/pat_1", headers=headers_alice)
    assert resp_alice.status_code == 200

    # Dr. Bob is NOT assigned to pat_1 and has no emergency access -> should be denied 403
    headers_bob = auth_headers("doc_2", "doctor")
    resp_bob = await client.get("/patients/pat_1", headers=headers_bob)
    assert resp_bob.status_code == 403
    assert "Access denied" in resp_bob.json()["detail"]
