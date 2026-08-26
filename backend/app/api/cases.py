from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.case import Case
from app.models.diagnosis import Diagnosis
from app.models.rule_finding import RuleFinding
from app.models.review import Review
from app.models.verification_result import VerificationResult
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from app.schemas.diagnosis import DiagnosisResponse
from app.schemas.rule_finding import RuleFindingResponse
from app.services.case_loader import seed_cases
from app.services.rule_engine import DeterministicRuleChecker
from app.services.ai_diagnostics import AIDiagnosisService
from app.services.comparison import ComparisonService

router = APIRouter()


@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_database_cases(db: Session = Depends(get_db)):
    """Seeds the database with 30 realistic Cisco Packet Tracer troubleshooting cases."""
    count = seed_cases(db)
    total = db.query(Case).count()
    return {
        "message": f"Successfully seeded {count} new cases from dataset.",
        "total_cases": total
    }


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db)):
    existing = db.query(Case).filter(Case.case_id == case_in.case_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case with ID '{case_in.case_id}' already exists."
        )
    case = Case(
        case_id=case_in.case_id,
        title=case_in.title,
        description=case_in.description,
        network_topology=case_in.network_topology or {},
        raw_configs=case_in.raw_configs or {},
        status=case_in.status or "OPEN"
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("/", response_model=List[CaseResponse])
def list_cases(
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Case)
    if status_filter:
        query = query.filter(Case.status == status_filter)
    if category_filter:
        query = query.filter(Case.description.contains(f"Category: {category_filter}"))
    return query.order_by(Case.id.asc()).offset(skip).limit(limit).all()


@router.get("/{id_or_case_id}")
def get_case(id_or_case_id: str, db: Session = Depends(get_db)):
    if id_or_case_id.isdigit():
        case = db.query(Case).options(
            joinedload(Case.diagnoses),
            joinedload(Case.rule_findings),
            joinedload(Case.reviews),
            joinedload(Case.verification_results)
        ).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).options(
            joinedload(Case.diagnoses),
            joinedload(Case.rule_findings),
            joinedload(Case.reviews),
            joinedload(Case.verification_results)
        ).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{id_or_case_id}' not found."
        )

    return {
        "id": case.id,
        "case_id": case.case_id,
        "title": case.title,
        "description": case.description,
        "network_topology": case.network_topology,
        "raw_configs": case.raw_configs,
        "status": case.status,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "diagnoses": case.diagnoses,
        "rule_findings": case.rule_findings,
        "reviews": case.reviews,
        "verification_results": case.verification_results,
    }


@router.post("/{id_or_case_id}/check-rules", response_model=List[RuleFindingResponse])
def run_case_rule_check(id_or_case_id: str, db: Session = Depends(get_db)):
    """Runs the Python Deterministic Rule Checker on the specified case."""
    if id_or_case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    checker = DeterministicRuleChecker(
        raw_configs=case.raw_configs or {},
        topology=case.network_topology or {}
    )
    raw_findings = checker.run_all_checks()

    # Clear previous rule findings for this case to avoid duplication
    db.query(RuleFinding).filter(RuleFinding.case_id == case.id).delete()

    created_findings = []
    for rf in raw_findings:
        finding = RuleFinding(
            case_id=case.id,
            rule_id=rf["rule_id"],
            rule_name=rf["rule_name"],
            category=rf["category"],
            severity=rf["severity"],
            status=rf["status"],
            affected_device=rf.get("affected_device"),
            affected_interface=rf.get("affected_interface"),
            message=rf["message"],
            details=rf.get("details", {})
        )
        db.add(finding)
        created_findings.append(finding)

    db.commit()
    for f in created_findings:
        db.refresh(f)

    return created_findings


@router.post("/{id_or_case_id}/diagnose", response_model=DiagnosisResponse)
def run_case_ai_diagnosis(id_or_case_id: str, db: Session = Depends(get_db)):
    """Runs the AI Diagnostic Service on the specified case with fallback mock mode."""
    if id_or_case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    # Fetch existing rule findings if any
    existing_findings = db.query(RuleFinding).filter(RuleFinding.case_id == case.id).all()
    rf_dicts = [
        {
            "rule_id": f.rule_id,
            "rule_name": f.rule_name,
            "category": f.category,
            "severity": f.severity,
            "affected_device": f.affected_device,
            "affected_interface": f.affected_interface,
            "message": f.message
        }
        for f in existing_findings
    ]

    ai_service = AIDiagnosisService()
    diag_res = ai_service.diagnose_case(
        case_id=case.case_id,
        title=case.title,
        description=case.description or "",
        topology=case.network_topology or {},
        raw_configs=case.raw_configs or {},
        rule_findings=rf_dicts
    )

    diag = Diagnosis(
        case_id=case.id,
        summary=diag_res.get("summary", "Diagnostic report"),
        root_cause=diag_res.get("root_cause", "Root cause identified"),
        confidence_score=diag_res.get("confidence", 0.9),
        evidence=diag_res.get("evidence", []),
        osi_layer=diag_res.get("osi_layer", "Layer 3 - Network"),
        next_command=diag_res.get("next_command", "show ip interface brief"),
        fix_steps=diag_res.get("fix_steps", []),
        suggested_commands=diag_res.get("suggested_commands", []),
        explanation=diag_res.get("explanation", ""),
        model_name=diag_res.get("model_name", "mock-ai-engine")
    )
    db.add(diag)
    if case.status == "OPEN":
        case.status = "IN_REVIEW"

    db.commit()
    db.refresh(diag)
    return diag


@router.post("/{id_or_case_id}/analyze")
def run_full_case_analysis(id_or_case_id: str, db: Session = Depends(get_db)):
    """
    Complete analysis pipeline:
    Case -> AI Diagnosis -> Python Rule Check -> Comparison
    """
    if id_or_case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

    # 1. Run Python Rule Check
    checker = DeterministicRuleChecker(
        raw_configs=case.raw_configs or {},
        topology=case.network_topology or {}
    )
    raw_findings = checker.run_all_checks()

    db.query(RuleFinding).filter(RuleFinding.case_id == case.id).delete()
    stored_findings = []
    for rf in raw_findings:
        finding = RuleFinding(
            case_id=case.id,
            rule_id=rf["rule_id"],
            rule_name=rf["rule_name"],
            category=rf["category"],
            severity=rf["severity"],
            status=rf["status"],
            affected_device=rf.get("affected_device"),
            affected_interface=rf.get("affected_interface"),
            message=rf["message"],
            details=rf.get("details", {})
        )
        db.add(finding)
        stored_findings.append(finding)
    db.commit()

    rf_dicts = [
        {
            "rule_id": f.rule_id,
            "rule_name": f.rule_name,
            "category": f.category,
            "severity": f.severity,
            "affected_device": f.affected_device,
            "affected_interface": f.affected_interface,
            "message": f.message,
            "details": f.details
        }
        for f in stored_findings
    ]

    # 2. Run AI Diagnosis
    ai_service = AIDiagnosisService()
    diag_res = ai_service.diagnose_case(
        case_id=case.case_id,
        title=case.title,
        description=case.description or "",
        topology=case.network_topology or {},
        raw_configs=case.raw_configs or {},
        rule_findings=rf_dicts
    )

    diag = Diagnosis(
        case_id=case.id,
        summary=diag_res.get("summary", "Diagnostic report"),
        root_cause=diag_res.get("root_cause", "Root cause identified"),
        confidence_score=diag_res.get("confidence", 0.95),
        evidence=diag_res.get("evidence", []),
        osi_layer=diag_res.get("osi_layer", "Layer 3 - Network"),
        next_command=diag_res.get("next_command", "show ip interface brief"),
        fix_steps=diag_res.get("fix_steps", []),
        suggested_commands=diag_res.get("suggested_commands", []),
        explanation=diag_res.get("explanation", ""),
        model_name=diag_res.get("model_name", "mock-ai-engine")
    )
    db.add(diag)
    if case.status == "OPEN":
        case.status = "IN_REVIEW"
    db.commit()
    db.refresh(diag)

    # 3. Compare AI Diagnosis vs Rule Findings
    comparison_res = ComparisonService.compare(
        diagnosis={
            "root_cause": diag.root_cause,
            "confidence": diag.confidence_score,
            "evidence": diag.evidence,
            "osi_layer": diag.osi_layer,
            "next_command": diag.next_command,
            "fix_steps": diag.fix_steps
        },
        rule_findings=rf_dicts
    )

    rf_response = [
        {
            "id": f.id,
            "case_id": f.case_id,
            "rule_id": f.rule_id,
            "rule_name": f.rule_name,
            "category": f.category,
            "severity": f.severity,
            "status": f.status,
            "affected_device": f.affected_device,
            "affected_interface": f.affected_interface,
            "message": f.message,
            "details": f.details,
            "created_at": f.created_at.isoformat() if f.created_at else None
        }
        for f in stored_findings
    ]

    return {
        "case_id": case.case_id,
        "title": case.title,
        "status": case.status,
        "ai_diagnosis": {
            "id": diag.id,
            "summary": diag.summary,
            "root_cause": diag.root_cause,
            "confidence": diag.confidence_score,
            "evidence": diag.evidence,
            "osi_layer": diag.osi_layer,
            "next_command": diag.next_command,
            "fix_steps": diag.fix_steps,
            "suggested_commands": diag.suggested_commands,
            "explanation": diag.explanation,
            "model_name": diag.model_name
        },
        "rule_findings": rf_response,
        "comparison": comparison_res
    }

