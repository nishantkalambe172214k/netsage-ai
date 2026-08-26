from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.case import Case
from app.models.rule_finding import RuleFinding
from app.schemas.rule_finding import RuleFindingCreate, RuleFindingResponse

router = APIRouter()


@router.post("/", response_model=RuleFindingResponse, status_code=status.HTTP_201_CREATED)
def create_rule_finding(finding_in: RuleFindingCreate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == finding_in.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {finding_in.case_id} not found."
        )

    finding = RuleFinding(
        case_id=finding_in.case_id,
        rule_id=finding_in.rule_id,
        rule_name=finding_in.rule_name,
        category=finding_in.category,
        severity=finding_in.severity,
        status=finding_in.status,
        affected_device=finding_in.affected_device,
        affected_interface=finding_in.affected_interface,
        message=finding_in.message,
        details=finding_in.details or {}
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)
    return finding


@router.get("/case/{case_id}", response_model=List[RuleFindingResponse])
def get_rule_findings_by_case(case_id: int, db: Session = Depends(get_db)):
    return db.query(RuleFinding).filter(RuleFinding.case_id == case_id).order_by(RuleFinding.created_at.desc()).all()
