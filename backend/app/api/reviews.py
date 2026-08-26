from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.case import Case
from app.models.diagnosis import Diagnosis
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter()


@router.post("/{id_or_case_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def submit_human_review(id_or_case_id: str, review_in: ReviewCreate, db: Session = Depends(get_db)):
    """
    Submits a Mandatory Human Review decision (ACCEPTED, EDITED, REJECTED).
    Requires human review before any AI diagnosis can be considered final or verified.
    """
    # Lookup case
    if id_or_case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{id_or_case_id}' not found.")

    # Find latest diagnosis for case if diagnosis_id not provided
    diag_id = review_in.diagnosis_id
    latest_diag = None
    if diag_id:
        latest_diag = db.query(Diagnosis).filter(Diagnosis.id == diag_id).first()
    else:
        latest_diag = db.query(Diagnosis).filter(Diagnosis.case_id == case.id).order_by(Diagnosis.created_at.desc()).first()
        if latest_diag:
            diag_id = latest_diag.id

    decision = review_in.decision.upper()
    if decision in ["APPROVED", "ACCEPT"]:
        decision = "ACCEPTED"
    elif decision == "EDIT":
        decision = "EDITED"
    elif decision == "REJECT":
        decision = "REJECTED"

    # Validation checks
    if decision == "EDITED" and not (review_in.review_notes and review_in.review_notes.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer notes/explanation is required when submitting an EDITED diagnosis."
        )

    if decision == "REJECTED" and not (review_in.rejection_reason and review_in.rejection_reason.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A rejection reason is required when REJECTING an AI diagnosis."
        )

    # Capture original diagnosis snapshot
    orig_diag = review_in.original_diagnosis or {}
    if not orig_diag and latest_diag:
        orig_diag = {
            "root_cause": latest_diag.root_cause,
            "confidence": latest_diag.confidence_score,
            "osi_layer": latest_diag.osi_layer,
            "evidence": latest_diag.evidence,
            "next_command": latest_diag.next_command,
            "fix_steps": latest_diag.fix_steps,
            "suggested_commands": latest_diag.suggested_commands
        }

    review = Review(
        case_id=case.id,
        diagnosis_id=diag_id,
        reviewer_name=review_in.reviewer_name or "Network Engineer",
        decision=decision,
        original_diagnosis=orig_diag,
        corrected_diagnosis=review_in.corrected_diagnosis or {},
        review_notes=review_in.review_notes,
        rejection_reason=review_in.rejection_reason,
        why_ai_incorrect=review_in.why_ai_incorrect,
        modified_commands=review_in.modified_commands or []
    )
    db.add(review)

    # State transition for Case
    if decision in ["ACCEPTED", "EDITED"]:
        case.status = "APPROVED"
    elif decision == "REJECTED":
        case.status = "REJECTED"

    db.commit()
    db.refresh(review)
    return review


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review_general(review_in: ReviewCreate, db: Session = Depends(get_db)):
    """General review submission by body case_id."""
    if not review_in.case_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="case_id is required in review payload.")
    return submit_human_review(str(review_in.case_id), review_in, db)


@router.get("/{id_or_case_id}", response_model=List[ReviewResponse])
def get_case_reviews(id_or_case_id: str, db: Session = Depends(get_db)):
    if id_or_case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{id_or_case_id}' not found.")

    return db.query(Review).filter(Review.case_id == case.id).order_by(Review.reviewed_at.desc()).all()


@router.get("/", response_model=List[ReviewResponse])
def list_all_reviews(
    decision: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Review)
    if decision:
        query = query.filter(Review.decision == decision.upper())
    return query.order_by(Review.reviewed_at.desc()).offset(skip).limit(limit).all()
