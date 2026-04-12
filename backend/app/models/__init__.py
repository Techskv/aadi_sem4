"""Models package initialization.

Import model modules so SQLAlchemy relationship targets are registered
before any mapper configuration occurs.
"""

from app.models.exam import AnswerKey, Exam, ReferenceDocument
from app.models.result import Result, TotalResult
from app.models.submission import ExtractedAnswer, Submission
from app.models.user import User, UserRole

__all__ = [
    "AnswerKey",
    "Exam",
    "ExtractedAnswer",
    "ReferenceDocument",
    "Result",
    "Submission",
    "TotalResult",
    "User",
    "UserRole",
]
