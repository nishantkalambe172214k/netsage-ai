from datetime import datetime
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, ConfigDict, Field


class CaseBase(BaseModel):
    case_id: str = Field(..., description="Unique case identifier, e.g. CASE-001")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    network_topology: Optional[Dict[str, Any]] = Field(default_factory=dict)
    raw_configs: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: str = Field(default="OPEN", description="OPEN, IN_REVIEW, APPROVED, REJECTED, RESOLVED, CLOSED")


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    network_topology: Optional[Dict[str, Any]] = None
    raw_configs: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class CaseResponse(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
