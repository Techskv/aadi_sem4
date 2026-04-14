"""
Exam and AnswerKey models.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.database import Base


class Exam(Base):
    """Exam model for storing exam metadata."""
    
    __tablename__ = "exams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    subject = Column(String(100), nullable=False)
    description = Column(Text)
    total_marks = Column(Float, default=0)
    duration_minutes = Column(Integer, default=60)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="exams")
    answer_keys = relationship("AnswerKey", back_populates="exam", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="exam")
    reference_documents = relationship("ReferenceDocument", back_populates="exam", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Exam {self.name}>"


class ReferenceDocument(Base):
    """Stores additional reference materials for an exam to be used for RAG."""
    
    __tablename__ = "reference_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content = Column(Text)  # Extracted text content
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    exam = relationship("Exam", back_populates="reference_documents")
    
    def __repr__(self):
        return f"<ReferenceDocument {self.filename} for Exam {self.exam_id}>"


class AnswerKey(Base):
    """Answer key model for storing correct answers and rubrics."""
    
    __tablename__ = "answer_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    question_no = Column(Integer, nullable=False)
    question_type = Column(String(20), nullable=False)  # MCQ, SHORT_ANSWER, SUBJECTIVE
    question_text = Column(Text)
    correct_answer = Column(Text)
    keywords = Column(JSON)  # For short answer matching
    rubric = Column(JSON)    # For subjective scoring
    max_marks = Column(Float, nullable=False)
    negative_marks = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    exam = relationship("Exam", back_populates="answer_keys")
    
    def __repr__(self):
        return f"<AnswerKey Q{self.question_no} for Exam {self.exam_id}>"
