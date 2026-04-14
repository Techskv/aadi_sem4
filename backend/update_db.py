from app.models.database import engine, Base
from app.models.user import User
from app.models.exam import Exam, ReferenceDocument, AnswerKey
from app.models.submission import Submission, ExtractedAnswer
from app.models.result import Result, TotalResult

print("Checking and creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database schema updated successfully (Added ReferenceDocument).")
