import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
import app.models  # ensure models are registered
from app.main import app

# Test SQLite in-memory database with StaticPool to share connection across sessions
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


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_full_troubleshooting_flow(client):
    # 1. Create Case
    case_data = {
        "case_id": "CASE-OSPF-002",
        "title": "OSPF Area 0 Neighbor Adjacency Stuck in EXSTART",
        "description": "R1 and R2 are connected on GigabitEthernet0/0/0. OSPF fails to form FULL state.",
        "network_topology": {"devices": ["R1", "R2"], "protocol": "OSPF"},
        "raw_configs": {
            "R1": "interface Gi0/0/0\n ip address 10.0.0.1 255.255.255.252\n ip mtu 1500\n router ospf 1\n network 10.0.0.0 0.0.0.3 area 0",
            "R2": "interface Gi0/0/0\n ip address 10.0.0.2 255.255.255.252\n ip mtu 1400\n router ospf 1\n network 10.0.0.0 0.0.0.3 area 0"
        },
        "status": "OPEN"
    }
    res = client.post("/api/cases/", json=case_data)
    assert res.status_code == 201
    created_case = res.json()
    case_db_id = created_case["id"]
    assert created_case["case_id"] == "CASE-OSPF-002"

    # 2. Add Rule Finding
    finding_data = {
        "case_id": case_db_id,
        "rule_id": "RULE_MTU_MISMATCH",
        "rule_name": "Interface MTU Mismatch on OSPF Link",
        "category": "ROUTING",
        "severity": "CRITICAL",
        "status": "FAIL",
        "affected_device": "R2",
        "affected_interface": "Gi0/0/0",
        "message": "MTU mismatch detected between R1 (1500) and R2 (1400) on link 10.0.0.0/30.",
        "details": {"r1_mtu": 1500, "r2_mtu": 1400}
    }
    res = client.post("/api/rule-findings/", json=finding_data)
    assert res.status_code == 201

    # 3. Add AI Diagnosis
    diag_data = {
        "case_id": case_db_id,
        "summary": "OSPF database exchange stuck in EXSTART due to MTU mismatch on link.",
        "root_cause": "R2 interface Gi0/0/0 has MTU 1400 while R1 has MTU 1500. During DBD packet exchange, MTU comparison fails.",
        "suggested_commands": [
            {
                "device": "R2",
                "commands": [
                    "interface GigabitEthernet0/0/0",
                    "ip mtu 1500"
                ]
            }
        ],
        "confidence_score": 0.99,
        "explanation": "OSPF requires matching MTU values by default on point-to-point links.",
        "model_name": "gemini-2.5-pro"
    }
    res = client.post("/api/diagnoses/", json=diag_data)
    assert res.status_code == 201
    created_diag = res.json()
    diag_id = created_diag["id"]

    # 4. Mandatory Human Review (HITL)
    review_data = {
        "case_id": case_db_id,
        "diagnosis_id": diag_id,
        "reviewer_name": "Lead Architect Bob",
        "decision": "APPROVED",
        "review_notes": "MTU 1500 is the standard for this transit link. Approved.",
        "modified_commands": []
    }
    res = client.post("/api/reviews/", json=review_data)
    assert res.status_code == 201
    created_review = res.json()
    review_id = created_review["id"]

    # 5. Verification Result
    verify_data = {
        "case_id": case_db_id,
        "review_id": review_id,
        "status": "PASSED",
        "test_summary": "show ip ospf neighbor shows FULL/BDR state.",
        "verification_output": {"state": "FULL", "neighbor_id": "10.0.0.1"}
    }
    res = client.post("/api/verification/", json=verify_data)
    assert res.status_code == 201

    # 6. Fetch Case by case_id string and verify aggregate response
    res = client.get("/api/cases/CASE-OSPF-002")
    assert res.status_code == 200
    case_detail = res.json()
    assert case_detail["status"] == "RESOLVED"
    assert len(case_detail["rule_findings"]) == 1
    assert len(case_detail["diagnoses"]) == 1
    assert len(case_detail["reviews"]) == 1
    assert len(case_detail["verification_results"]) == 1
