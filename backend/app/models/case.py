from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Topology details (devices, interfaces, links, VLAN assignments)
    network_topology = Column(JSON, nullable=True, default=dict)
    
    # Raw configuration dumps or show commands per device
    raw_configs = Column(JSON, nullable=True, default=dict)
    
    # Status: OPEN, IN_REVIEW, APPROVED, REJECTED, RESOLVED, CLOSED
    status = Column(String(32), default="OPEN", index=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    diagnoses = relationship(
        "Diagnosis",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="desc(Diagnosis.created_at)"
    )
    rule_findings = relationship(
        "RuleFinding",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="desc(RuleFinding.created_at)"
    )
    reviews = relationship(
        "Review",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="desc(Review.reviewed_at)"
    )
    verification_results = relationship(
        "VerificationResult",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="desc(VerificationResult.verified_at)"
    )
