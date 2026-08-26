import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base
from app.models.case import Case
from app.models.diagnosis import Diagnosis
from app.models.rule_finding import RuleFinding
from app.models.review import Review
from app.models.verification_result import VerificationResult


@pytest.fixture
def db_session():
    # In-memory SQLite with StaticPool for testing
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_create_case_and_relationships(db_session):
    # 1. Create a Case
    case = Case(
        case_id="CASE-PT-001",
        title="VLAN 10 and 20 Routing Failure",
        description="Hosts in VLAN 10 cannot ping hosts in VLAN 20 through Router R1 sub-interfaces.",
        network_topology={
            "devices": ["R1", "SW1", "PC1", "PC2"],
            "links": [
                {"from": "PC1:Fa0", "to": "SW1:Fa0/1", "vlan": 10},
                {"from": "PC2:Fa0", "to": "SW1:Fa0/2", "vlan": 20},
                {"from": "SW1:Gi0/1", "to": "R1:Gi0/0", "mode": "trunk"}
            ]
        },
        raw_configs={
            "SW1": "interface FastEthernet0/1\n switchport access vlan 10\ninterface GigabitEthernet0/1\n switchport mode trunk",
            "R1": "interface GigabitEthernet0/0.10\n encapsulation dot1Q 10\n ip address 192.168.10.1 255.255.255.0\ninterface GigabitEthernet0/0.20\n encapsulation dot1Q 30\n ip address 192.168.20.1 255.255.255.0"
        },
        status="OPEN"
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)

    assert case.id is not None
    assert case.case_id == "CASE-PT-001"
    assert case.status == "OPEN"

    # 2. Add Rule Finding (Deterministic rule check)
    finding = RuleFinding(
        case_id=case.id,
        rule_id="RULE_DOT1Q_VLAN_MISMATCH",
        rule_name="Sub-interface 802.1Q VLAN Tag Mismatch",
        category="VLAN",
        severity="CRITICAL",
        status="FAIL",
        affected_device="R1",
        affected_interface="GigabitEthernet0/0.20",
        message="Sub-interface Gi0/0.20 has encapsulation dot1Q 30 configured, but serves subnet for VLAN 20 (expected dot1Q 20).",
        details={"configured_vlan": 30, "expected_vlan": 20}
    )
    db_session.add(finding)
    db_session.commit()

    # 3. Add AI Diagnosis
    diagnosis = Diagnosis(
        case_id=case.id,
        summary="VLAN encapsulation tag mismatch on Router-on-a-Stick sub-interface Gi0/0.20.",
        root_cause="Router R1 interface Gi0/0.20 is configured with 802.1Q tag 30 instead of tag 20, dropping all VLAN 20 tagged frames.",
        suggested_commands=[
            {
                "device": "R1",
                "commands": [
                    "interface GigabitEthernet0/0.20",
                    "encapsulation dot1Q 20",
                    "ip address 192.168.20.1 255.255.255.0"
                ]
            }
        ],
        confidence_score=0.98,
        explanation="Packet Tracer router sub-interface must have matching 802.1Q tags with the switch access VLAN.",
        model_name="gemini-2.5-pro"
    )
    db_session.add(diagnosis)
    db_session.commit()

    # 4. Add Mandatory Human Review (HITL)
    review = Review(
        case_id=case.id,
        diagnosis_id=diagnosis.id,
        reviewer_name="Senior NetEng Alice",
        decision="APPROVED",
        review_notes="Verified root cause and commands against topology diagram. Fix is safe and accurate.",
        modified_commands=[]
    )
    db_session.add(review)
    case.status = "APPROVED"
    db_session.commit()

    # 5. Add Verification Result
    verification = VerificationResult(
        case_id=case.id,
        review_id=review.id,
        status="PASSED",
        test_summary="Simulated ping test from PC1 (192.168.10.10) to PC2 (192.168.20.10) succeeded with 0% packet loss.",
        verification_output={
            "ping_success": True,
            "packets_sent": 5,
            "packets_received": 5,
            "re_evaluated_rules_passed": True
        }
    )
    db_session.add(verification)
    case.status = "RESOLVED"
    db_session.commit()

    # Verify all relations queryable via Case
    refreshed_case = db_session.query(Case).filter(Case.id == case.id).first()
    assert len(refreshed_case.rule_findings) == 1
    assert refreshed_case.rule_findings[0].rule_id == "RULE_DOT1Q_VLAN_MISMATCH"
    assert len(refreshed_case.diagnoses) == 1
    assert refreshed_case.diagnoses[0].confidence_score == 0.98
    assert len(refreshed_case.reviews) == 1
    assert refreshed_case.reviews[0].decision == "APPROVED"
    assert len(refreshed_case.verification_results) == 1
    assert refreshed_case.verification_results[0].status == "PASSED"
    assert refreshed_case.status == "RESOLVED"
