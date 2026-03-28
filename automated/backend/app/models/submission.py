"""
Submission model for answer sheet uploads.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.database import Base


class SubmissionStatus(str, enum.Enum):
    """Submission status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    EVALUATED = "evaluated"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"


class Submission(Base):
    """Submission model for storing uploaded answer sheets."""
    
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20))  # pdf, png, jpg, etc.
    original_filename = Column(String(255))
    question_paper_path = Column(String(500), nullable=True)
    question_paper_original_filename = Column(String(255), nullable=True)
    status = Column(String(20), default=SubmissionStatus.PENDING.value)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    student = relationship("User", back_populates="submissions")
    exam = relationship("Exam", back_populates="submissions")
    extracted_answers = relationship("ExtractedAnswer", back_populates="submission", cascade="all, delete-orphan")
    results = relationship("Result", back_populates="submission", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Submission {self.id} by User {self.student_id}>"


class ExtractedAnswer(Base):
    """Extracted answers from OCR processing."""
    
    __tablename__ = "extracted_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    question_no = Column(Integer, nullable=False)
    extracted_text = Column(Text)
    confidence_score = Column(Float)  # OCR confidence
    bounding_box = Column(String(200))  # JSON coords of text region
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submission = relationship("Submission", back_populates="extracted_answers")
    
    def __repr__(self):
        return f"<ExtractedAnswer Q{self.question_no} for Submission {self.submission_id}>"
