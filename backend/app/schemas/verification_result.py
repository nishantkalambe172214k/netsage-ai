from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class VerificationResultBase(BaseModel):
    status: str = Field(default="PENDING", description="PASSED, FAILED, PARTIAL, PENDING")
    test_summary: Optional[str] = None
    verification_output: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VerificationResultCreate(VerificationResultBase):
    case_id: int
    review_id: Optional[int] = None


class VerificationResultResponse(VerificationResultBase):
    id: int
    case_id: int
    review_id: Optional[int] = None
    verified_at: datetime

    model_config = ConfigDict(from_attributes=True)
