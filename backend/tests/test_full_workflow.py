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


def test_complete_human_governed_lifecycle(client):
    # Step 1: Seed 30 cases
    seed_res = client.post("/api/cases/seed")
    assert seed_res.status_code == 200

    # Step 2: Run complete pipeline analysis on CASE-GW-005
    # (Workstation Configured with Inactive Default Gateway IP)
    analyze_res = client.post("/api/cases/CASE-GW-005/analyze")
    assert analyze_res.status_code == 200
    analysis = analyze_res.json()
    assert analysis["case_id"] == "CASE-GW-005"
    assert "ai_diagnosis" in analysis
    assert len(analysis["rule_findings"]) >= 1
    assert "comparison" in analysis

    # Step 3: Human Review - Reviewer EDITS diagnosis to add specific interface details
    diag = analysis["ai_diagnosis"]
    review_res = client.post("/api/reviews/CASE-GW-005", json={
        "reviewer_name": "Senior NetEng Jordan",
        "decision": "EDITED",
        "original_diagnosis": diag,
        "corrected_diagnosis": {
            "root_cause": "Workstation PC4 default gateway 192.168.1.254 is unreachable; router R1 Gi0/0 is 192.168.1.1.",
            "confidence": 0.99,
            "osi_layer": "Layer 3 - Network",
            "next_command": "show ip interface brief",
            "fix_steps": ["Set PC4 default gateway to 192.168.1.1"]
        },
        "review_notes": "Confirmed topology and router interface IP. Updated client gateway from 192.168.1.254 to 192.168.1.1.",
        "why_ai_incorrect": "Refined general gateway diagnosis with exact client IP and router interface name."
    })
    assert review_res.status_code == 201
    review = review_res.json()
    assert review["decision"] == "EDITED"

    # Step 4: Verification - Engineer records manual verification PASSED
    verify_res = client.post("/api/verification/CASE-GW-005", json={
        "review_id": review["id"],
        "status": "PASSED",
        "test_summary": "PC4 successfully pinged 8.8.8.8 and local gateway 192.168.1.1 with 0% loss.",
        "notes": "Verified in Packet Tracer topology simulation.",
        "verification_evidence": {"ping_success_rate": 1.0, "rtt_ms": 2.1}
    })
    assert verify_res.status_code == 201
    assert verify_res.json()["status"] == "PASSED"

    # Step 5: Check Case status is now RESOLVED
    case_res = client.get("/api/cases/CASE-GW-005")
    assert case_res.json()["status"] == "RESOLVED"

    # Step 6: Verify Dashboard reflects the complete workflow
    dash_res = client.get("/api/dashboard/")
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert dash["kpis"]["total_cases"] == 30
    assert dash["kpis"]["human_reviewed"] >= 1
    assert dash["kpis"]["edited"] >= 1
    assert dash["kpis"]["verified_passed"] >= 1
