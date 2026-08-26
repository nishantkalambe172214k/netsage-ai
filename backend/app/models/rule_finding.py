from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class RuleFinding(Base):
    __tablename__ = "rule_findings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    rule_id = Column(String(64), nullable=False, index=True)
    rule_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)  # INTERFACE, VLAN, IP_ADDRESSING, ROUTING, ACL, STP, SECURITY
    
    # Severity: INFO, WARNING, CRITICAL
    severity = Column(String(32), nullable=False, default="WARNING")
    
    # Status: FAIL, PASS, WARNING
    status = Column(String(32), nullable=False, default="FAIL")
    
    affected_device = Column(String(64), nullable=True)
    affected_interface = Column(String(64), nullable=True)
    
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="rule_findings")
