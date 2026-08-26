import pytest
from app.services.ai_diagnostics import AIDiagnosisService


def test_mock_ai_diagnosis_schema():
    service = AIDiagnosisService(api_key=None)  # Explicitly trigger mock mode
    result = service.diagnose_case(
        case_id="CASE-VLAN-001",
        title="Inter-VLAN Routing Blocked by Sub-interface Dot1Q Tag Mismatch",
        description="PC1 in VLAN 10 cannot ping PC2 in VLAN 20 via Router-on-a-Stick R1.",
        topology={"devices": ["R1", "SW1", "PC1", "PC2"]},
        raw_configs={"R1": "interface GigabitEthernet0/0.20\n encapsulation dot1Q 30"}
    )

    assert "root_cause" in result
    assert "confidence" in result
    assert "evidence" in result
    assert "osi_layer" in result
    assert "next_command" in result
    assert "fix_steps" in result

    assert isinstance(result["root_cause"], str)
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0
    assert isinstance(result["evidence"], list)
    assert isinstance(result["osi_layer"], str)
    assert isinstance(result["next_command"], str)
    assert isinstance(result["fix_steps"], list)
    assert result["model_name"] == "mock-ai-engine"
    assert "dot1Q" in result["root_cause"] or "VLAN" in result["root_cause"]


def test_mock_ai_diagnosis_custom_case():
    service = AIDiagnosisService(api_key=None)
    result = service.diagnose_case(
        case_id="CASE-CUSTOM-999",
        title="Custom Lab Gateway Issue",
        description="Custom description",
        topology={"devices": ["R1"]},
        raw_configs={"R1": "interface Gi0/0\n shutdown"}
    )

    assert result["root_cause"] is not None
    assert result["confidence"] > 0.0
    assert len(result["evidence"]) >= 1
    assert result["model_name"] == "mock-ai-engine"
