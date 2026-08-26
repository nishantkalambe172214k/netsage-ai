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
    
    reviewer_name = Column(String(128), nullable=False)
    
    # Decision: APPROVED, REJECTED, MODIFIED
    decision = Column(String(32), nullable=False, default="APPROVED")
    
    # Mandatory or optional review notes justifying decision
    review_notes = Column(Text, nullable=True)
    
    # Modified commands if human reviewer adjusted the AI recommendation
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
