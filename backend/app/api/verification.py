from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.case import Case
from app.models.review import Review
from app.models.verification_result import VerificationResult
from app.schemas.verification_result import VerificationResultCreate, VerificationResultResponse

router = APIRouter()


@router.post("/", response_model=VerificationResultResponse, status_code=status.HTTP_201_CREATED)
def record_verification_result(vr_in: VerificationResultCreate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == vr_in.case_id).first()
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID {vr_in.case_id} not found."
        )

    if vr_in.review_id:
        review = db.query(Review).filter(Review.id == vr_in.review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with ID {vr_in.review_id} not found."
            )

    vr = VerificationResult(
        case_id=vr_in.case_id,
        review_id=vr_in.review_id,
        status=vr_in.status,
        test_summary=vr_in.test_summary,
        verification_output=vr_in.verification_output or {}
    )
    db.add(vr)

    # If verification PASSED, mark case as RESOLVED
    if vr_in.status == "PASSED":
        case.status = "RESOLVED"

    db.commit()
    db.refresh(vr)
    return vr


@router.get("/case/{case_id}", response_model=List[VerificationResultResponse])
def get_verification_by_case(case_id: int, db: Session = Depends(get_db)):
    return db.query(VerificationResult).filter(VerificationResult.case_id == case_id).order_by(VerificationResult.verified_at.desc()).all()
