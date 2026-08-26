from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, ConfigDict, Field


class DiagnosisBase(BaseModel):
    summary: str
    root_cause: str
    suggested_commands: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    confidence_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    explanation: Optional[str] = None
    model_name: Optional[str] = "gemini-2.5-pro"


class DiagnosisCreate(DiagnosisBase):
    case_id: int


class DiagnosisResponse(DiagnosisBase):
    id: int
    case_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
