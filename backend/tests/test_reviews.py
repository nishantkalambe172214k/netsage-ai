import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
import app.models  # noqa: F401
from app.main import app
from app.models.case import Case
from app.models.diagnosis import Diagnosis
from app.models.review import Review

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


def test_human_review_accept(client):
    # Setup case + diagnosis
    case_res = client.post("/api/cases/", json={
        "case_id": "CASE-REV-001",
        "title": "Test Case for Review Accept",
        "description": "VLAN issue"
    })
    case_id = case_res.json()["id"]

    diag_res = client.post("/api/diagnoses/", json={
        "case_id": case_id,
        "summary": "AI diagnosis summary",
        "root_cause": "Dot1Q tag mismatch",
        "confidence_score": 0.95,
        "osi_layer": "Layer 2 - Data Link"
    })
    diag_id = diag_res.json()["id"]

    # Submit ACCEPT review
    review_res = client.post("/api/reviews/CASE-REV-001", json={
        "reviewer_name": "Engineer Alice",
        "decision": "ACCEPTED",
        "review_notes": "Looks solid, approved."
    })
    assert review_res.status_code == 201
    rev = review_res.json()
    assert rev["decision"] == "ACCEPTED"
    assert rev["reviewer_name"] == "Engineer Alice"

    # Check case status transitioned to APPROVED
    c_check = client.get("/api/cases/CASE-REV-001").json()
    assert c_check["status"] == "APPROVED"


def test_human_review_edit(client):
    # Setup case + diagnosis
    case_res = client.post("/api/cases/", json={
        "case_id": "CASE-REV-002",
        "title": "Test Case for Review Edit",
        "description": "Routing issue"
    })
    case_id = case_res.json()["id"]

    diag_res = client.post("/api/diagnoses/", json={
        "case_id": case_id,
        "summary": "AI initial guess",
        "root_cause": "Wrong area in OSPF",
        "confidence_score": 0.70,
        "osi_layer": "Layer 3 - Network"
    })
    diag_id = diag_res.json()["id"]

    # Submit EDITED review (requires reviewer_notes)
    review_res = client.post("/api/reviews/CASE-REV-002", json={
        "reviewer_name": "Senior Architect Bob",
        "decision": "EDITED",
        "original_diagnosis": {"root_cause": "Wrong area in OSPF", "confidence": 0.70},
        "corrected_diagnosis": {
            "root_cause": "MTU mismatch 1400 vs 1500 on point-to-point link",
            "confidence": 0.99,
            "osi_layer": "Layer 3 - Network",
            "next_command": "show ip ospf neighbor",
            "fix_steps": ["interface Gi0/0", "ip mtu 1500"]
        },
        "review_notes": "AI misidentified the issue as OSPF area mismatch. Link MTU was the actual root cause.",
        "why_ai_incorrect": "AI ignored MTU difference in config lines."
    })
    assert review_res.status_code == 201
    rev = review_res.json()
    assert rev["decision"] == "EDITED"
    assert rev["corrected_diagnosis"]["confidence"] == 0.99
    assert "MTU mismatch" in rev["corrected_diagnosis"]["root_cause"]
    assert "AI misidentified" in rev["review_notes"]


def test_human_review_edit_requires_notes(client):
    case_res = client.post("/api/cases/", json={
        "case_id": "CASE-REV-003",
        "title": "Test Case for Edit Validation",
        "description": "Validation test"
    })

    # Attempt to edit WITHOUT reviewer notes -> should fail with 400 or 422
    review_res = client.post("/api/reviews/CASE-REV-003", json={
        "reviewer_name": "Engineer Charlie",
        "decision": "EDITED",
        "review_notes": "",
        "corrected_diagnosis": {"root_cause": "Corrected text"}
    })
    assert review_res.status_code in [400, 422]


def test_human_review_reject_requires_reason(client):
    case_res = client.post("/api/cases/", json={
        "case_id": "CASE-REV-004",
        "title": "Test Case for Reject Validation",
        "description": "Validation test"
    })

    # Attempt to reject WITHOUT rejection reason -> should fail with 400 or 422
    review_res = client.post("/api/reviews/CASE-REV-004", json={
        "reviewer_name": "Engineer Dave",
        "decision": "REJECTED",
        "rejection_reason": ""
    })
    assert review_res.status_code in [400, 422]

    # Valid REJECT with reason
    valid_res = client.post("/api/reviews/CASE-REV-004", json={
        "reviewer_name": "Engineer Dave",
        "decision": "REJECTED",
        "rejection_reason": "Proposed commands would wipe production ACL."
    })
    assert valid_res.status_code == 201
    assert valid_res.json()["decision"] == "REJECTED"

    c_check = client.get("/api/cases/CASE-REV-004").json()
    assert c_check["status"] == "REJECTED"
