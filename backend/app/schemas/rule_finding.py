from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, Field


class RuleFindingBase(BaseModel):
    rule_id: str
    rule_name: str
    category: str
    severity: str = Field(default="WARNING", description="INFO, WARNING, CRITICAL")
    status: str = Field(default="FAIL", description="FAIL, PASS, WARNING")
    affected_device: Optional[str] = None
    affected_interface: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RuleFindingCreate(RuleFindingBase):
    case_id: int


class RuleFindingResponse(RuleFindingBase):
    id: int
    case_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
