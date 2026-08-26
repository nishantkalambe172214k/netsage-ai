from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.case import Case
from app.models.review import Review
from app.models.verification_result import VerificationResult
from app.schemas.verification_result import VerificationResultCreate, VerificationResultResponse

router = APIRouter()


@router.post("/{id_or_case_id}", response_model=VerificationResultResponse, status_code=status.HTTP_201_CREATED)
def submit_case_verification(
    id_or_case_id: str,
    vr_in: VerificationResultCreate,
    db: Session = Depends(get_db)
):
    """
    Submits a post-remediation verification result (PASSED, FAILED, PARTIAL).
    Transitions case to RESOLVED only when verification status is PASSED.
    """
    if id_or_case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{id_or_case_id}' not found.")

    review_id = vr_in.review_id
    if not review_id:
        latest_review = db.query(Review).filter(Review.case_id == case.id).order_by(Review.reviewed_at.desc()).first()
        if latest_review:
            review_id = latest_review.id

    v_status = vr_in.status.upper()

    vr = VerificationResult(
        case_id=case.id,
        review_id=review_id,
        status=v_status,
        test_summary=vr_in.test_summary or f"Manual verification result: {v_status}",
        notes=vr_in.notes or vr_in.test_summary,
        verification_evidence=vr_in.verification_evidence or {},
        verification_output=vr_in.verification_output or vr_in.verification_evidence or {}
    )
    db.add(vr)

    # State transition: only mark RESOLVED if PASSED
    if v_status == "PASSED":
        case.status = "RESOLVED"
    elif v_status == "FAILED":
        case.status = "VERIFICATION_FAILED"
    elif v_status == "PARTIAL":
        case.status = "PARTIAL"

    db.commit()
    db.refresh(vr)
    return vr


@router.post("/", response_model=VerificationResultResponse, status_code=status.HTTP_201_CREATED)
def create_verification_general(vr_in: VerificationResultCreate, db: Session = Depends(get_db)):
    if not vr_in.case_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="case_id is required.")
    return submit_case_verification(str(vr_in.case_id), vr_in, db)


@router.get("/{id_or_case_id}", response_model=List[VerificationResultResponse])
def get_case_verification_results(id_or_case_id: str, db: Session = Depends(get_db)):
    if id_or_case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{id_or_case_id}' not found.")

    return db.query(VerificationResult).filter(VerificationResult.case_id == case.id).order_by(VerificationResult.verified_at.desc()).all()


@router.get("/", response_model=List[VerificationResultResponse])
def list_all_verification_results(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(VerificationResult)
    if status:
        query = query.filter(VerificationResult.status == status.upper())
    return query.order_by(VerificationResult.verified_at.desc()).offset(skip).limit(limit).all()
