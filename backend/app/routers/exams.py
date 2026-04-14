"""
Exams router - CRUD for exams and answer keys.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.user import User, UserRole
from app.models.exam import Exam, AnswerKey
from app.schemas.schemas import ExamCreate, ExamResponse, ExamListResponse, AnswerKeyCreate, AnswerKeyResponse
from app.utils.security import get_current_user, require_teacher
from app.services.ocr_service import ocr_service
from app.services.rag_service import rag_service
from app.models.exam import ReferenceDocument


router = APIRouter()


@router.get("/", response_model=List[ExamListResponse])
async def list_exams(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all available exams."""
    query = db.query(Exam).filter(Exam.is_active == 1)
    
    # Students see only active exams, teachers/admins see all
    if current_user.role == UserRole.STUDENT:
        query = query.filter(Exam.is_active == 1)
    
    exams = query.offset(skip).limit(limit).all()
    return exams


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get exam details by ID."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exam not found"
        )
    
    # Students cannot see answer keys
    if current_user.role == UserRole.STUDENT:
        exam.answer_keys = []
    
    return exam


@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    exam_data: ExamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Create a new exam (Teacher/Admin only)."""
    # Create exam
    new_exam = Exam(
        name=exam_data.name,
        subject=exam_data.subject,
        description=exam_data.description,
        duration_minutes=exam_data.duration_minutes,
        created_by=current_user.id
    )
    
    db.add(new_exam)
    db.flush()  # Get the ID before adding answer keys
    
    # Add answer keys if provided
    total_marks = 0
    if exam_data.answer_keys:
        for ak_data in exam_data.answer_keys:
            answer_key = AnswerKey(
                exam_id=new_exam.id,
                question_no=ak_data.question_no,
                question_type=ak_data.question_type,
                question_text=ak_data.question_text,
                correct_answer=ak_data.correct_answer,
                keywords=ak_data.keywords,
                rubric=ak_data.rubric,
                max_marks=ak_data.max_marks,
                negative_marks=ak_data.negative_marks
            )
            db.add(answer_key)
            total_marks += ak_data.max_marks
    
    new_exam.total_marks = total_marks
    db.commit()
    db.refresh(new_exam)
    
    return new_exam


@router.post("/{exam_id}/answer-keys", response_model=AnswerKeyResponse, status_code=status.HTTP_201_CREATED)
async def add_answer_key(
    exam_id: int,
    ak_data: AnswerKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Add an answer key to an exam."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check if question already exists
    existing = db.query(AnswerKey).filter(
        AnswerKey.exam_id == exam_id,
        AnswerKey.question_no == ak_data.question_no
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Answer key for question {ak_data.question_no} already exists"
        )
    
    answer_key = AnswerKey(
        exam_id=exam_id,
        question_no=ak_data.question_no,
        question_type=ak_data.question_type,
        question_text=ak_data.question_text,
        correct_answer=ak_data.correct_answer,
        keywords=ak_data.keywords,
        rubric=ak_data.rubric,
        max_marks=ak_data.max_marks,
        negative_marks=ak_data.negative_marks
    )
    
    db.add(answer_key)
    
    # Update total marks
    exam.total_marks += ak_data.max_marks
    
    db.commit()
    db.refresh(answer_key)
    
    return answer_key


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Soft delete an exam."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    exam.is_active = 0
    db.commit()


@router.post("/{exam_id}/reference-docs", status_code=status.HTTP_201_CREATED)
async def upload_reference_document(
    exam_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Upload reference material (textbook, notes) for RAG context during evaluation."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
        
    file_ext = file.filename.split(".")[-1].lower()
    
    # 1. Save file locally
    # Reuse submission upload path logic or create a dedicated reference folder
    ref_dir = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "reference_docs")
    os.makedirs(ref_dir, exist_ok=True)
    
    import uuid
    safe_filename = f"ref_{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(ref_dir, safe_filename)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
        
    # 2. Extract text from the reference document
    try:
        extracted_text = ocr_service.process_submission(file_path, file_ext)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process reference document: {e}")
        
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No text could be extracted from the document.")

    # 3. Save record in database
    ref_doc = ReferenceDocument(
        exam_id=exam_id,
        filename=file.filename,
        file_path=file_path,
        content=extracted_text
    )
    db.add(ref_doc)
    db.commit()
    db.refresh(ref_doc)
    
    # 4. Index in Vector Store (RAG)
    success = rag_service.index_document(exam_id, extracted_text, file.filename)
    
    return {
        "id": ref_doc.id, 
        "filename": ref_doc.filename, 
        "indexed": success,
        "message": "Reference material uploaded and indexed for RAG."
    }

import os
