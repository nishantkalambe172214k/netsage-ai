from datetime import datetime
from typing import Optional, Any, List, Dict
from pydantic import BaseModel, ConfigDict, Field


class DiagnosisBase(BaseModel):
    summary: str
    root_cause: str
    confidence_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    evidence: Optional[List[str]] = Field(default_factory=list)
    osi_layer: Optional[str] = Field(default="Layer 3 - Network")
    next_command: Optional[str] = Field(default="show ip interface brief")
    fix_steps: Optional[List[str]] = Field(default_factory=list)
    suggested_commands: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    explanation: Optional[str] = None
    model_name: Optional[str] = "mock-ai-engine"


class DiagnosisCreate(DiagnosisBase):
    case_id: int


class DiagnosisResponse(DiagnosisBase):
    id: int
    case_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
