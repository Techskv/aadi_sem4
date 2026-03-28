"""
Results router - View and manage evaluation results.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.database import get_db
from app.models.user import User, UserRole
from app.models.submission import Submission
from app.models.result import Result, TotalResult, EvaluationType
from app.schemas.schemas import ResultResponse, QuestionResult, ManualReviewRequest
from app.utils.security import get_current_user, require_teacher


router = APIRouter()


@router.get("/submission/{submission_id}", response_model=ResultResponse)
async def get_submission_results(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get evaluation results for a submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Access control
    if current_user.role == UserRole.STUDENT:
        if submission.student_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # If submission failed, return clear error immediately
    if submission.status == "failed":
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=422,
            content={
                "failed": True,
                "status": "failed",
                "detail": "Evaluation failed. Please try uploading again. Check that your file has readable text."
            }
        )

    # Get question-wise results (exclude question_no=0 which is the full-text record)
    results = (
        db.query(Result)
        .filter(Result.submission_id == submission_id, Result.question_no > 0)
        .order_by(Result.question_no)
        .all()
    )
    total_result = db.query(TotalResult).filter(TotalResult.submission_id == submission_id).first()

    if not results:
        # Results not ready yet — check if submission is still processing
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=202,
            content={
                "processing": True,
                "status": submission.status,
                "detail": "Results are still being processed. Please wait."
            }
        )

    question_results = []
    for r in results:
        question_results.append(QuestionResult(
            question_no=r.question_no,
            marks_obtained=round(float(r.marks_obtained or 0), 2),
            max_marks=round(float(r.max_marks or 10), 2),
            evaluation_type=r.evaluation_type,
            feedback=r.feedback,
            keywords_matched=r.keywords_matched.split(",") if r.keywords_matched else None
        ))

    # Recalculate live totals from question results (sanity check)
    live_obtained = round(sum(float(r.marks_obtained or 0) for r in results), 2)
    live_max = round(sum(float(r.max_marks or 10) for r in results), 2)
    live_pct = round((live_obtained / live_max * 100) if live_max > 0 else 0, 2)

    return ResultResponse(
        submission_id=submission_id,
        total_marks=live_obtained,
        max_marks=live_max,
        percentage=live_pct,
        grade=total_result.grade if total_result else None,
        ai_report_card=total_result.ai_report_card if total_result else None,
        questions=question_results,
        is_published=bool(total_result and total_result.is_published)
    )



@router.get("/review-queue")
async def get_review_queue(
    exam_id: int = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Get submissions pending manual review (Teacher only)."""
    query = db.query(Submission).filter(Submission.status == "review_required")
    
    if exam_id:
        query = query.filter(Submission.exam_id == exam_id)
    
    submissions = query.offset(skip).limit(limit).all()
    
    return [
        {
            "submission_id": s.id,
            "exam_id": s.exam_id,
            "student_id": s.student_id,
            "submitted_at": s.submitted_at
        }
        for s in submissions
    ]


@router.put("/submission/{submission_id}/question/{question_no}")
async def manual_review(
    submission_id: int,
    question_no: int,
    review_data: ManualReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Submit manual review marks for a question (Teacher only)."""
    result = db.query(Result).filter(
        Result.submission_id == submission_id,
        Result.question_no == question_no
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # Validate marks
    if review_data.marks_obtained > result.max_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Marks cannot exceed maximum ({result.max_marks})"
        )
    
    # Update result
    result.manual_score = review_data.marks_obtained
    result.marks_obtained = review_data.marks_obtained
    result.feedback = review_data.feedback
    result.evaluation_type = EvaluationType.MANUAL.value
    result.reviewed_by = current_user.id
    result.reviewed_at = datetime.utcnow()
    
    db.commit()
    
    db.commit()
    
    # Recalculate total immediately
    _update_total_result(db, submission_id)
    
    return {"message": "Review submitted successfully"}


@router.post("/submission/{submission_id}/finalize")
async def finalize_review(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Mark review as complete and update status."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    submission.status = "completed"
    
    # Ensure totals are up to date
    _update_total_result(db, submission_id)
    
    db.commit()
    return {"message": "Review finalized"}


@router.post("/submission/{submission_id}/publish")
async def publish_results(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher)
):
    """Publish results to make them visible to student (Teacher only)."""
    total_result = db.query(TotalResult).filter(TotalResult.submission_id == submission_id).first()
    
    if not total_result:
        raise HTTPException(status_code=404, detail="Results not found")
    
    total_result.is_published = 1
    total_result.published_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Results published successfully"}


def _update_total_result(db: Session, submission_id: int):
    """Helper to update total result after reviews."""
    results = (
        db.query(Result)
        .filter(Result.submission_id == submission_id, Result.question_no > 0)
        .all()
    )

    total_marks = round(sum(float(r.marks_obtained or 0) for r in results), 2)
    max_marks = round(sum(float(r.max_marks or 10) for r in results), 2)
    percentage = round((total_marks / max_marks * 100) if max_marks > 0 else 0, 2)
    grade = _calculate_grade(percentage)

    
    total_result = db.query(TotalResult).filter(TotalResult.submission_id == submission_id).first()
    
    if total_result:
        total_result.total_marks = total_marks
        total_result.max_marks = max_marks
        total_result.percentage = percentage
        total_result.grade = grade
    else:
        total_result = TotalResult(
            submission_id=submission_id,
            total_marks=total_marks,
            max_marks=max_marks,
            percentage=percentage,
            grade=grade
        )
        db.add(total_result)


def _calculate_grade(percentage: float) -> str:
    """Calculate grade from percentage."""
    if percentage >= 90:
        return "A+"
    elif percentage >= 80:
        return "A"
    elif percentage >= 70:
        return "B+"
    elif percentage >= 60:
        return "B"
    elif percentage >= 50:
        return "C"
    elif percentage >= 40:
        return "D"
    else:
        return "F"


@router.get("/submission/{submission_id}/download")
async def download_report(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download evaluation report as PDF."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    # Access control
    if current_user.role == UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    total_result = db.query(TotalResult).filter(TotalResult.submission_id == submission_id).first()
    if not total_result:
         raise HTTPException(status_code=404, detail="Results not found")
         
    if current_user.role == UserRole.STUDENT and not total_result.is_published:
        raise HTTPException(status_code=403, detail="Results not yet published")
        
    # Fetch data
    student = db.query(User).filter(User.id == submission.student_id).first()
    exam = db.query(Exam).filter(Exam.id == submission.exam_id).first()
    results = db.query(Result).filter(Result.submission_id == submission_id).all()
    
    # Generate PDF
    from app.services.report_service import report_service
    from fastapi.responses import Response
    
    pdf_content = report_service.generate_pdf_report(
        submission, total_result, results, student, exam.name
    )
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=report_{submission_id}.pdf"
        }
    )
