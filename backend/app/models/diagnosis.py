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
    
    # Suggested CLI remediation commands: list of dicts, e.g. [{"device": "R1", "commands": ["int g0/0", "no shut"]}]
    suggested_commands = Column(JSON, nullable=True, default=list)
    
    # Confidence score from 0.0 to 1.0
    confidence_score = Column(Float, nullable=True, default=0.0)
    
    # Technical explanation of root cause and why fix resolves it
    explanation = Column(Text, nullable=True)
    
    # Model used (e.g., "gemini-2.5-pro", "rule-assisted-llm")
    model_name = Column(String(64), nullable=True, default="gemini-2.5-pro")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="diagnoses")
    reviews = relationship("Review", back_populates="diagnosis")
