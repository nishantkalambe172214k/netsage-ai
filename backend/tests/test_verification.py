import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
import app.models  # noqa: F401
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_verification_passed_resolves_case(client):
    client.post("/api/cases/", json={
        "case_id": "CASE-VER-001",
        "title": "Verification Test Case",
        "description": "Testing Passed Status"
    })

    # Submit verification PASSED
    res = client.post("/api/verification/CASE-VER-001", json={
        "status": "PASSED",
        "test_summary": "100% ping success across subnets",
        "notes": "Verified in Packet Tracer"
    })
    assert res.status_code == 201
    assert res.json()["status"] == "PASSED"

    # Verify Case transitioned to RESOLVED
    c = client.get("/api/cases/CASE-VER-001").json()
    assert c["status"] == "RESOLVED"


def test_verification_failed_status(client):
    client.post("/api/cases/", json={
        "case_id": "CASE-VER-002",
        "title": "Verification Test Case 2",
        "description": "Testing Failed Status"
    })

    res = client.post("/api/verification/CASE-VER-002", json={
        "status": "FAILED",
        "test_summary": "Pings still timing out with 100% packet loss",
        "notes": "Fix did not resolve the issue"
    })
    assert res.status_code == 201
    assert res.json()["status"] == "FAILED"

    c = client.get("/api/cases/CASE-VER-002").json()
    assert c["status"] == "VERIFICATION_FAILED"


def test_verification_partial_status(client):
    client.post("/api/cases/", json={
        "case_id": "CASE-VER-003",
        "title": "Verification Test Case 3",
        "description": "Testing Partial Status"
    })

    res = client.post("/api/verification/CASE-VER-003", json={
        "status": "PARTIAL",
        "test_summary": "Local VLAN ping works, inter-VLAN still drops",
        "notes": "Partial connectivity restored"
    })
    assert res.status_code == 201
    assert res.json()["status"] == "PARTIAL"

    c = client.get("/api/cases/CASE-VER-003").json()
    assert c["status"] == "PARTIAL"
