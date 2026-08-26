from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator


class VerificationResultBase(BaseModel):
    status: str = Field(default="PASSED", description="PASSED, FAILED, PARTIAL")
    test_summary: Optional[str] = None
    notes: Optional[str] = None
    verification_evidence: Optional[Dict[str, Any]] = Field(default_factory=dict)
    verification_output: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ["PASSED", "FAILED", "PARTIAL", "PENDING"]:
            raise ValueError("Status must be PASSED, FAILED, or PARTIAL.")
        return v_upper


class VerificationResultCreate(VerificationResultBase):
    case_id: Optional[int] = None
    review_id: Optional[int] = None


class VerificationResultResponse(VerificationResultBase):
    id: int
    case_id: int
    review_id: Optional[int] = None
    verified_at: datetime

    model_config = ConfigDict(from_attributes=True)
