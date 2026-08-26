from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    diagnosis_id = Column(Integer, ForeignKey("diagnoses.id", ondelete="SET NULL"), nullable=True, index=True)
    
    reviewer_name = Column(String(128), nullable=False, default="Network Engineer")
    
    # Decision: ACCEPTED, EDITED, REJECTED
    decision = Column(String(32), nullable=False, default="ACCEPTED")
    
    # Original AI diagnosis payload snapshot
    original_diagnosis = Column(JSON, nullable=True, default=dict)
    
    # Human-corrected diagnosis payload (if decision == EDITED)
    corrected_diagnosis = Column(JSON, nullable=True, default=dict)
    
    # Reviewer notes/explanation (mandatory for EDITED)
    review_notes = Column(Text, nullable=True)
    
    # Rejection reason (mandatory for REJECTED)
    rejection_reason = Column(Text, nullable=True)
    
    # Why AI was incorrect or incomplete (for Responsible AI audit log)
    why_ai_incorrect = Column(Text, nullable=True)
    
    # Modified CLI commands for quick access
    modified_commands = Column(JSON, nullable=True, default=list)
    
    reviewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="reviews")
    diagnosis = relationship("Diagnosis", back_populates="reviews")
    verification_results = relationship(
        "VerificationResult",
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="desc(VerificationResult.verified_at)"
    )
