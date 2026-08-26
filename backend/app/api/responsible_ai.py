from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.responsible_ai import seed_responsible_ai_examples, get_responsible_ai_records

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
def get_responsible_ai_log(db: Session = Depends(get_db)):
    """
    Returns all Responsible AI records where human engineers corrected or rejected AI recommendations.
    Provides full auditability: AI Recommendation -> Human Problem Identification -> Human Correction -> Final Diagnosis.
    """
    records = get_responsible_ai_records(db)
    return {
        "total_corrections": len(records),
        "target_met": len(records) >= 5,
        "records": records
    }


@router.post("/seed-examples", status_code=status.HTTP_200_OK)
def seed_examples(db: Session = Depends(get_db)):
    """Seeds the 5 authentic human-corrected AI troubleshooting cases into the database."""
    seeded = seed_responsible_ai_examples(db)
    records = get_responsible_ai_records(db)
    return {
        "message": f"Successfully seeded {seeded} Responsible AI correction examples.",
        "total_corrections": len(records),
        "target_met": len(records) >= 5
    }
