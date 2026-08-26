from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.case import Case
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse

router = APIRouter()


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
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Case)
    if status_filter:
        query = query.filter(Case.status == status_filter)
    return query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{id_or_case_id}")
def get_case(id_or_case_id: str, db: Session = Depends(get_db)):
    # Support lookup by integer ID or string case_id
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


@router.put("/{id_or_case_id}", response_model=CaseResponse)
def update_case(id_or_case_id: str, case_in: CaseUpdate, db: Session = Depends(get_db)):
    if id_or_case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(id_or_case_id)).first()
    else:
        case = db.query(Case).filter(Case.case_id == id_or_case_id).first()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{id_or_case_id}' not found."
        )

    update_data = case_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)
    return case
