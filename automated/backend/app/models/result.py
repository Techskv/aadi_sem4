"""
Result model for storing evaluation results.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.database import Base


class EvaluationType(str, enum.Enum):
    """Evaluation type enumeration."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    HYBRID = "hybrid"


class Result(Base):
    """Result model for storing evaluation outcomes."""
    
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    question_no = Column(Integer, nullable=False)
    marks_obtained = Column(Float, default=0)
    max_marks = Column(Float, nullable=False)
    evaluation_type = Column(String(20), default=EvaluationType.AUTOMATIC.value)
    auto_score = Column(Float)  # Score from automated evaluation
    manual_score = Column(Float)  # Score from manual review
    feedback = Column(Text)
    keywords_matched = Column(Text)  # JSON list of matched keywords
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    submission = relationship("Submission", back_populates="results")
    reviewer = relationship("User", back_populates="reviewed_results")
    
    def __repr__(self):
        return f"<Result Q{self.question_no} - {self.marks_obtained}/{self.max_marks}>"


class TotalResult(Base):
    """Aggregated result for a submission."""
    
    __tablename__ = "total_results"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), unique=True, nullable=False)
    total_marks = Column(Float, default=0)
    max_marks = Column(Float, default=0)
    percentage = Column(Float, default=0)
    grade = Column(String(5))
    ai_report_card = Column(Text, nullable=True)
    is_published = Column(Integer, default=0)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TotalResult {self.total_marks}/{self.max_marks} ({self.grade})>"
