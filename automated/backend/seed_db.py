from app.models.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.exam import Exam, AnswerKey
from app.models.submission import Submission, ExtractedAnswer
from app.models.result import Result, TotalResult
from app.utils.security import hash_password

def seed_data():
    db = SessionLocal()
    
    # 1. Create a default teacher if not exists
    teacher = db.query(User).filter(User.email == "teacher@test.com").first()
    if not teacher:
        teacher = User(
            name="Test Teacher",
            email="teacher@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.TEACHER,
            is_active=1
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        print(f"Created teacher: {teacher.email}")

    # 2. Create a default student if not exists
    student = db.query(User).filter(User.email == "student@test.com").first()
    if not student:
        student = User(
            name="Test Student",
            email="student@test.com",
            password_hash=hash_password("password123"),
            role=UserRole.STUDENT,
            is_active=1
        )
        db.add(student)
        db.commit()
        db.refresh(student)
        print(f"Created student: {student.email}")

    # 3. Create a test exam if not exists
    exam = db.query(Exam).filter(Exam.name == "Physics Basics").first()
    if not exam:
        exam = Exam(
            name="Physics Basics",
            subject="Physics",
            description="Fundamental physics questions",
            duration_minutes=60,
            total_marks=30,
            created_by=teacher.id,
            is_active=1
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)
        print(f"Created exam: {exam.name}")

        # Add some answer keys
        q1 = AnswerKey(
            exam_id=exam.id,
            question_no=1,
            question_type="short_answer",
            question_text="What is the unit of force?",
            correct_answer="Newton",
            keywords=["Newton", "N"],
            max_marks=10
        )
        q2 = AnswerKey(
            exam_id=exam.id,
            question_no=2,
            question_type="subjective",
            question_text="Explain Newton's second law of motion.",
            correct_answer="Force is equal to the rate of change of momentum. F=ma.",
            keywords=["acceleration", "mass", "force", "F=ma"],
            max_marks=20
        )
        db.add(q1)
        db.add(q2)
        db.commit()
        print("Created answer keys")
    else:
        print("Exam already exists")

    db.close()

if __name__ == "__main__":
    seed_data()
