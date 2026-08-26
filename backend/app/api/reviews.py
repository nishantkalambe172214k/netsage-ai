from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.case import Case
from app.models.diagnosis import Diagnosis
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter()


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def submit_human_review(review_in: ReviewCreate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == review_in.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {review_in.case_id} not found."
        )

    if review_in.diagnosis_id:
        diagnosis = db.query(Diagnosis).filter(Diagnosis.id == review_in.diagnosis_id).first()
        if not diagnosis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diagnosis with ID {review_in.diagnosis_id} not found."
            )

    review = Review(
        case_id=review_in.case_id,
        diagnosis_id=review_in.diagnosis_id,
        reviewer_name=review_in.reviewer_name,
        decision=review_in.decision,
        review_notes=review_in.review_notes,
        modified_commands=review_in.modified_commands or []
    )
    db.add(review)

    # Transition case status based on human decision
    if review_in.decision == "APPROVED":
        case.status = "APPROVED"
    elif review_in.decision == "MODIFIED":
        case.status = "APPROVED"  # Approved with modifications
    elif review_in.decision == "REJECTED":
        case.status = "REJECTED"

    db.commit()
    db.refresh(review)
    return review


@router.get("/case/{case_id}", response_model=List[ReviewResponse])
def get_reviews_by_case(case_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.case_id == case_id).order_by(Review.reviewed_at.desc()).all()
