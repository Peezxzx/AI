from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import office_router
from backend.office_store import OfficeStore


def make_client(tmp_path):
    office_router.office_store = OfficeStore(tmp_path / "office.db")
    app = FastAPI()
    app.include_router(office_router.router)
    return TestClient(app)


def test_command_endpoint_queues_risky_approval(tmp_path):
    client = make_client(tmp_path)
    res = client.post("/api/office/command", json={"text": "sell XAUUSD now", "source": "test", "target": "mina"})
    assert res.status_code == 200
    assert res.json()["command"]["status"] == "waiting_owner_approval"

    approvals = client.get("/api/office/approvals", params={"status": "waiting_owner_approval"}).json()["approvals"]
    assert len(approvals) == 1
    assert approvals[0]["detail"] == "sell XAUUSD now"


def test_approval_decision_endpoint_updates_status(tmp_path):
    client = make_client(tmp_path)
    client.post("/api/office/command", json={"text": "publish report", "source": "test", "target": "mina"})
    approval_id = client.get("/api/office/approvals").json()["approvals"][0]["id"]

    res = client.post(f"/api/office/approvals/{approval_id}/reject", json={"note": "not now"})

    assert res.status_code == 200
    assert res.json()["approval"]["status"] == "rejected"
    assert client.get("/api/office/approvals", params={"status": "waiting_owner_approval"}).json()["approvals"] == []
