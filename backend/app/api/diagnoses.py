from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.case import Case
from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisResponse

router = APIRouter()


@router.post("/", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
def create_diagnosis(diag_in: DiagnosisCreate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == diag_in.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {diag_in.case_id} not found."
        )

    diag = Diagnosis(
        case_id=diag_in.case_id,
        summary=diag_in.summary,
        root_cause=diag_in.root_cause,
        suggested_commands=diag_in.suggested_commands or [],
        confidence_score=diag_in.confidence_score or 0.0,
        explanation=diag_in.explanation,
        model_name=diag_in.model_name or "gemini-2.5-pro"
    )
    db.add(diag)
    # Automatically flag case as IN_REVIEW if OPEN
    if case.status == "OPEN":
        case.status = "IN_REVIEW"
    db.commit()
    db.refresh(diag)
    return diag


@router.get("/case/{case_id}", response_model=List[DiagnosisResponse])
def get_diagnoses_by_case(case_id: int, db: Session = Depends(get_db)):
    return db.query(Diagnosis).filter(Diagnosis.case_id == case_id).order_by(Diagnosis.created_at.desc()).all()
