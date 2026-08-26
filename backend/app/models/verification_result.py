from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Status: PASSED, FAILED, PARTIAL
    status = Column(String(32), nullable=False, default="PASSED")
    
    test_summary = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Detailed verification outputs/evidence (e.g. ping results, show command diffs)
    verification_evidence = Column(JSON, nullable=True, default=dict)
    
    # Legacy alias support for verification_output
    verification_output = Column(JSON, nullable=True, default=dict)
    
    verified_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="verification_results")
    review = relationship("Review", back_populates="verification_results")
