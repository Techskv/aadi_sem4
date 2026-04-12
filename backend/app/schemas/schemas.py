"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============ User Schemas ============

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.STUDENT


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


# ============ Exam Schemas ============

class AnswerKeyCreate(BaseModel):
    question_no: int = Field(..., ge=1)
    question_type: str = Field(..., pattern="^(MCQ|SHORT_ANSWER|SUBJECTIVE)$")
    question_text: Optional[str] = None
    correct_answer: Optional[str] = None
    keywords: Optional[List[str]] = None
    rubric: Optional[dict] = None
    max_marks: float = Field(..., gt=0)
    negative_marks: float = Field(default=0, ge=0)


class AnswerKeyResponse(AnswerKeyCreate):
    id: int
    exam_id: int

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    subject: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    duration_minutes: int = Field(default=60, ge=1)


class ExamCreate(ExamBase):
    answer_keys: Optional[List[AnswerKeyCreate]] = None


class ExamResponse(ExamBase):
    id: int
    total_marks: float
    created_by: int
    is_active: int
    created_at: datetime
    answer_keys: List[AnswerKeyResponse] = []

    class Config:
        from_attributes = True


class ExamListResponse(BaseModel):
    id: int
    name: str
    subject: str
    total_marks: float
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Submission Schemas ============

class SubmissionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    EVALUATED = "evaluated"
    REVIEW_REQUIRED = "review_required"
    COMPLETED = "completed"
    FAILED = "failed"


class SubmissionResponse(BaseModel):
    id: int
    student_id: int
    exam_id: int
    file_type: Optional[str]
    original_filename: Optional[str]
    question_paper_original_filename: Optional[str] = None
    status: str
    submitted_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ Result Schemas ============

class QuestionResult(BaseModel):
    question_no: int
    marks_obtained: float
    max_marks: float
    evaluation_type: str
    feedback: Optional[str] = None
    keywords_matched: Optional[List[str]] = None


class ResultResponse(BaseModel):
    submission_id: int
    total_marks: float
    max_marks: float
    percentage: float
    grade: Optional[str]
    ai_report_card: Optional[str] = None
    questions: List[QuestionResult]
    is_published: bool


class ManualReviewRequest(BaseModel):
    question_no: int
    marks_obtained: float = Field(..., ge=0)
    feedback: Optional[str] = None
