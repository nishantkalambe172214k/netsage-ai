from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReviewBase(BaseModel):
    reviewer_name: str = Field(default="Network Engineer", description="Name of reviewing engineer")
    decision: str = Field(..., description="ACCEPTED, EDITED, REJECTED (or ACCEPT, EDIT, REJECT, APPROVED)")
    original_diagnosis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    corrected_diagnosis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    review_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    why_ai_incorrect: Optional[str] = None
    modified_commands: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_decision_fields(self):
        dec = self.decision.upper()
        if dec in ["APPROVED", "ACCEPT"]:
            dec = "ACCEPTED"
            self.decision = "ACCEPTED"
        elif dec == "EDIT":
            dec = "EDITED"
            self.decision = "EDITED"
        elif dec == "REJECT":
            dec = "REJECTED"
            self.decision = "REJECTED"

        if dec not in ["ACCEPTED", "EDITED", "REJECTED"]:
            raise ValueError("Decision must be ACCEPTED, EDITED, or REJECTED.")

        if dec == "EDITED" and not (self.review_notes and self.review_notes.strip()):
            raise ValueError("Reviewer notes/explanation is required when editing an AI diagnosis.")

        if dec == "REJECTED" and not (self.rejection_reason and self.rejection_reason.strip()):
            raise ValueError("A rejection reason is required when rejecting an AI diagnosis.")

        return self


class ReviewCreate(ReviewBase):
    case_id: Optional[int] = None
    diagnosis_id: Optional[int] = None


class ReviewResponse(ReviewBase):
    id: int
    case_id: int
    diagnosis_id: Optional[int] = None
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)
