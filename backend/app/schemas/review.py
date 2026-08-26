from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    reviewer_name: str
    decision: str = Field(..., description="APPROVED, REJECTED, MODIFIED")
    review_notes: Optional[str] = None
    modified_commands: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class ReviewCreate(ReviewBase):
    case_id: int
    diagnosis_id: Optional[int] = None


class ReviewResponse(ReviewBase):
    id: int
    case_id: int
    diagnosis_id: Optional[int] = None
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)
