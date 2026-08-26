import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
import app.models  # noqa: F401
from app.main import app
from app.models.case import Case

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


def test_seed_cases_and_verify_30_cases(client):
    # 1. Trigger database seed endpoint
    res = client.post("/api/cases/seed")
    assert res.status_code == 200
    data = res.json()
    assert data["total_cases"] == 30

    # 2. List all cases
    res = client.get("/api/cases/?limit=100")
    assert res.status_code == 200
    cases_list = res.json()
    assert len(cases_list) == 30

    # Verify categories present
    case_titles = [c["title"] for c in cases_list]
    assert any("VLAN" in t for t in case_titles)
    assert any("Gateway" in t or "Default" in t for t in case_titles)
    assert any("DHCP" in t for t in case_titles)
    assert any("DNS" in t for t in case_titles)
    assert any("OSPF" in t or "Route" in t or "Routing" in t or "EIGRP" in t for t in case_titles)
    assert any("ACL" in t or "Access" in t for t in case_titles)
    assert any("NAT" in t for t in case_titles)
    assert any("Wireless" in t or "SSID" in t or "WPA2" in t for t in case_titles)


def test_complete_end_to_end_troubleshooting_workflow(client):
    # 1. Seed cases
    client.post("/api/cases/seed")

    # 2. Test analyze endpoint on CASE-VLAN-001
    # This runs Case -> AI Diagnosis -> Python Rule Check -> Comparison
    res = client.post("/api/cases/CASE-VLAN-001/analyze")
    assert res.status_code == 200
    analysis = res.json()

    assert analysis["case_id"] == "CASE-VLAN-001"
    assert analysis["status"] == "IN_REVIEW"

    # Verify AI Diagnosis Payload contract
    diag = analysis["ai_diagnosis"]
    assert "root_cause" in diag
    assert "confidence" in diag
    assert "evidence" in diag
    assert "osi_layer" in diag
    assert "next_command" in diag
    assert "fix_steps" in diag
    assert diag["confidence"] > 0.8

    # Verify Rule Findings
    findings = analysis["rule_findings"]
    assert len(findings) >= 1
    vlan_finding = next((f for f in findings if "VLAN" in f["rule_id"] or "VLAN" in f["category"]), None)
    assert vlan_finding is not None

    # Verify Comparison
    comparison = analysis["comparison"]
    assert "alignment_score" in comparison
    assert "status" in comparison
    assert comparison["status"] in ["FULL_ALIGNMENT", "PARTIAL_ALIGNMENT"]
    assert comparison["matched_rules_count"] >= 1

    # 3. Perform Mandatory Human Review (HITL)
    diag_id = diag["id"]
    case_db_res = client.get("/api/cases/CASE-VLAN-001")
    case_db_id = case_db_res.json()["id"]

    review_payload = {
        "case_id": case_db_id,
        "diagnosis_id": diag_id,
        "reviewer_name": "Senior Network Architect",
        "decision": "APPROVED",
        "review_notes": "AI diagnosis matches deterministic rule findings. Approved remediation commands for Router R1 sub-interface.",
        "modified_commands": []
    }
    review_res = client.post("/api/reviews/", json=review_payload)
    assert review_res.status_code == 201
    created_review = review_res.json()

    # 4. Perform Verification
    verification_payload = {
        "case_id": case_db_id,
        "review_id": created_review["id"],
        "status": "PASSED",
        "test_summary": "Re-ran Packet Tracer ping test across VLAN 10 and VLAN 20. 100% success rate.",
        "verification_output": {"ping_success_rate": 1.0, "latency_ms": 1.8}
    }
    verify_res = client.post("/api/verification/", json=verification_payload)
    assert verify_res.status_code == 201

    # 5. Verify final Case state is RESOLVED
    final_case_res = client.get("/api/cases/CASE-VLAN-001")
    assert final_case_res.status_code == 200
    final_case = final_case_res.json()
    assert final_case["status"] == "RESOLVED"
    assert len(final_case["diagnoses"]) >= 1
    assert len(final_case["rule_findings"]) >= 1
    assert len(final_case["reviews"]) >= 1
    assert len(final_case["verification_results"]) >= 1
