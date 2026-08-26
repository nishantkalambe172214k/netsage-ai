from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    summary = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    
    # Confidence score from 0.0 to 1.0
    confidence_score = Column(Float, nullable=True, default=0.0)
    
    # Evidence list (e.g. ["Interface Gi0/1 is administratively down", "IP conflict on 192.168.1.1"])
    evidence = Column(JSON, nullable=True, default=list)
    
    # OSI Layer (e.g. "Layer 1 - Physical", "Layer 2 - Data Link", "Layer 3 - Network", etc.)
    osi_layer = Column(String(64), nullable=True)
    
    # Next recommended troubleshooting command (e.g. "show ip interface brief")
    next_command = Column(String(255), nullable=True)
    
    # Ordered list of remediation steps/commands
    fix_steps = Column(JSON, nullable=True, default=list)
    
    # Suggested CLI remediation commands: list of dicts [{"device": "R1", "commands": [...]}]
    suggested_commands = Column(JSON, nullable=True, default=list)
    
    # Technical explanation of root cause
    explanation = Column(Text, nullable=True)
    
    # Model used (e.g. "gemini-2.5-pro", "mock-ai-engine")
    model_name = Column(String(64), nullable=True, default="mock-ai-engine")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="diagnoses")
    reviews = relationship("Review", back_populates="diagnosis")
